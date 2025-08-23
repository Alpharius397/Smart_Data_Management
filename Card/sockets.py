from typing import Any
from Card.types import ConfirmJson, ReadJson
from Report.views import ReportData, SubjectProto
from University.models import Schema
from User.models import (
    aget_post_by_ID,
    ais_authenticated,
    ais_manager,
    User,
)
from tools.encrypt import (
    decrypt_key,
    decrypt_bytes,
)
from tools.errors import TokenExpired
from tools.get_image import expand_image
from Logs.loggers import APP_LOG, LogStructure
from tools.types import NullInt
from tools.utils import setSwalAlert
from Card.models import Card
from constants import DEFAULT_ERROR
from Main.models import (
    AsyncRedisConnection,
    ReadToken,
    RedisDataBase,
    WriteToken,
)
from channels.generic.websocket import AsyncWebsocketConsumer, DenyConnection  # type: ignore
from asgiref.sync import async_to_sync
from django.template.loader import render_to_string  # type: ignore
from channels.layers import get_channel_layer  # type: ignore
from protobuf.build.cardData import v3_pb2
from base64 import b64encode
from Card.types import CardReport


async def agetCardData(cardID: str, cardData: str) -> dict[str, Any]:
    context: CardReport | dict = {}

    card = await Card.objects.aget(cardID=cardID)
    decrypted_data = decrypt_bytes(decrypt_key(card.decryption_key), cardData)

    protobufData = v3_pb2.CardData().FromString(decrypted_data)

    report_data = ReportData(
        images={
            i: expand_image(b64encode(j).decode())
            for i, j in protobufData.image.items()
        },
        personal=dict(protobufData.personal.items()),
        sem_data={
            i: {
                a: SubjectProto(id=b.id, total=b.total, other=dict(b.other.items()))
                for a, b in j.subject.items()
            }
            for i, j in protobufData.semester.items()
        },
    )

    context.update((await Schema.agetSchema(protobufData.header.schema)))
    context.update(
        (
            await aget_post_by_ID(
                protobufData.header.university,
                protobufData.header.institute,
                protobufData.header.branch,
            )
        )
    )
    columns: dict[int, set[str]] = {}

    for sem, subs in report_data["sem_data"].items():
        if sem not in columns:
            columns[sem] = set()

        for meta in subs.values():
            columns[sem].update(meta["other"].keys())

    context.update({"columns": columns})
    context.update(report_data)
    return context


def getCardData(card: Card, sem: NullInt = None) -> dict[str, Any]:
    context: CardReport | dict = {}

    decrypted_data = decrypt_bytes(decrypt_key(card.decryption_key), card.data)

    protobufData = v3_pb2.CardData().FromString(decrypted_data)

    report_data = ReportData(
        images={
            i: expand_image(b64encode(j).decode())
            for i, j in protobufData.image.items()
        },
        personal=dict(protobufData.personal.items()),
        sem_data={
            i: {
                a: SubjectProto(id=b.id, total=b.total, other=dict(b.other.items()))
                for a, b in j.subject.items()
            }
            for i, j in protobufData.semester.items()
            if ((sem is None) or ((sem is not None) and (i == sem)))
        },
    )

    context.update(Schema.getSchema(protobufData.header.schema))
    columns: dict[int, set[str]] = {}

    for sem, subs in report_data["sem_data"].items():
        if sem not in columns:
            columns[sem] = set()

        for meta in subs.values():
            columns[sem].update(meta["other"].keys())

    context.update({"columns": columns})
    context.update(report_data)
    return context


def cardWriteWebSocket(token: str, data: ConfirmJson):
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(token, {"type": "card.write", **data})  # type: ignore
    except Exception:
        pass


class CardWriteExeConsumer(AsyncWebsocketConsumer):
    user: User
    taskID: int
    idx: int
    token: str

    async def auth_user(self) -> bool:
        try:
            user: User = self.user
            managerFlag = await ais_manager(user)
            authFlag = await ais_authenticated(user)

            return bool(managerFlag and authFlag)
        except Exception:
            return False

    async def auth_token(self) -> bool:
        try:
            async with AsyncRedisConnection(RedisDataBase.CARD_WRITE_TOKEN) as redis:
                data: WriteToken | ReadToken = await redis.getDict(self.token)  # type: ignore

                processing = data.get("processing", None)
                ID = data.get("ID", -1)

                if (not isinstance(processing, bool)) or (
                    isinstance(processing, bool) and (processing is not True)
                ):
                    raise TokenExpired()

                user = await User.objects.aget(id=ID)

                return self.user.id == user.id

        except Exception:
            return False

    async def connect(self) -> None:
        try:
            self.taskID = self.scope["url_route"]["kwargs"]["id"]
            self.idx = self.scope["url_route"]["kwargs"]["idx"]
            self.token = self.scope["url_route"]["kwargs"]["token"]
            self.user = self.scope["user"]

            self.room_group_name = self.token

            tokenFlags = await self.auth_token()
            userFlags = await self.auth_user()

            if not (tokenFlags and userFlags):
                raise DenyConnection("Unauthenticated User")

            await self.channel_layer.group_add(self.room_group_name, self.channel_name)  # type: ignore

            await self.accept()

        except DenyConnection as f:
            raise f

        except Exception:
            raise DenyConnection("Invalid URL found!")

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)  # type: ignore

    # Receive message from WebSocket
    async def receive(self, text_data: str):  # type: ignore
        APP_LOG.write_error(LogStructure().set_error(Exception("No Entry Here")))

    async def card_write(self, event: ConfirmJson):
        status = event.get("status", "none")
        message = event.get("message", DEFAULT_ERROR)
        context = setSwalAlert(title="Card Write")

        match status:
            case "true":
                setSwalAlert(context, message, "success")
            case "false":
                setSwalAlert(context, message, "warning")
            case _:
                setSwalAlert(context, message)

        await self.send(
            text_data=render_to_string("Report/HTMX/write/end.html", context=context),
            close=True,
        )


def cardReadWebSocket(token: str, data: ReadJson):  # type: ignore
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(  # type: ignore
            token,
            {"type": "card.read", **data},
        )

    except Exception:
        pass


class CardReadExeConsumer(AsyncWebsocketConsumer):
    user: User
    token: str

    async def auth_user(self) -> bool:
        try:
            user: User = self.user
            managerFlag = await ais_manager(user)
            authFlag = await ais_authenticated(user)

            return bool(managerFlag and authFlag)
        except Exception:
            return False

    async def auth_token(self) -> bool:
        try:
            async with AsyncRedisConnection(RedisDataBase.CARD_READ_TOKEN) as redis:
                data: WriteToken | ReadToken = await redis.getDict(self.token)  # type: ignore

                processing = data.get("processing", None)
                ID = data.get("ID", -1)

                if (not isinstance(processing, bool)) or (
                    isinstance(processing, bool) and (processing is not True)
                ):
                    raise TokenExpired()

                user = await User.objects.aget(id=ID)

                return self.user.id == user.id

        except Exception:
            return False

    async def connect(self) -> None:
        try:
            self.token = self.scope["url_route"]["kwargs"]["token"]
            self.user = self.scope["user"]

            self.room_group_name = self.token

            tokenFlags = await self.auth_token()
            userFlags = await self.auth_user()

            if not (tokenFlags and userFlags):
                raise DenyConnection("Unauthenticated User")

            await self.channel_layer.group_add(self.room_group_name, self.channel_name)  # type: ignore

            await self.accept()

        except DenyConnection as f:
            APP_LOG.write_error(LogStructure().set_error(f))
            raise f

        except Exception as e:
            APP_LOG.write_error(LogStructure().set_error(e))
            raise DenyConnection("Invalid URL found!")

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)  # type: ignore

    async def receive(self, text_data: str):  # type: ignore
        APP_LOG.write_error(LogStructure().set_error(Exception("No Entry Here")))

    async def card_read(self, event: ReadJson) -> None:
        status = event["status"]
        cardID = event["card"]
        data = event["data"]
        message = event["data"]
        context: dict = {}

        with open("sample/test.proto.txt", "r") as f:
            data = f.read()

        match status:
            case "true":
                try:
                    context = await agetCardData(cardID, data)
                    setSwalAlert(context, message, "success")

                except Exception:
                    context["messages"] = ["Failed to parse card data!"]

            case _:
                context["messages"] = ["Failed to read card data"]

        await self.send(
            text_data=render_to_string("Dash/HTMX/report.html", context=context),
            close=True,
        )
