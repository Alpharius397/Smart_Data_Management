import json
from Main.settings import settingsInterface as settings
from Logs.loggers import LogStructure, APP_LOG
from tools.encrypt import decrypt_data, certificateHash
from User.models import is_authenticated, is_manager, User
from channels.generic.websocket import AsyncWebsocketConsumer, DenyConnection  # type: ignore
from tools.token import hash_token
from asgiref.sync import sync_to_async, async_to_sync
from django.template.loader import render_to_string
from typing import TypedDict
from constants import DEFAULT_ERROR, READ_TOKEN
from channels.layers import get_channel_layer  # type: ignore
from tools.utils import ReportStructure, deconstructSubjects, processSubjects


def cardReadWebSocket(token: str, cardID: str, data: str, status: str):  # type: ignore
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(  # type: ignore
            token,
            {"type": "cardRead", "status": status, "cardID": cardID, "data": data},
        )
    except Exception as e:
        pass


class CardReadExeConsumer(AsyncWebsocketConsumer):
    class CardData(TypedDict):
        status: str
        cardID: str
        data: str

    user: User
    token: str

    async def auth_user(self) -> bool:
        managerFlag = await sync_to_async(is_manager)(self.user)
        authFlag = await sync_to_async(is_authenticated)(self.user)
        return bool(managerFlag and authFlag)

    async def auth_token(self) -> bool:
        sessionToken = self.scope["session"].get(READ_TOKEN, "None")
        return bool(hash_token(sessionToken, self.user.id) == self.token)

    async def connect(self) -> None:
        self.token = self.scope["url_route"]["kwargs"]["token"]
        self.user = self.scope["user"]
        self.room_group_name = self.token

        tokenFlags = await self.auth_token()
        userFlags = await self.auth_user()

        if not (tokenFlags and userFlags):
            raise DenyConnection("Unauthenticated User")

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)  # type: ignore

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)  # type: ignore

    # Receive message from WebSocket
    async def receive(self, text_data):  # type: ignore
        text_data_json: CardReadExeConsumer.CardData = json.loads(text_data)  # type: ignore

        status = text_data_json.get("status", "")
        cardID = text_data_json.get("cardID", "")
        data = text_data_json.get("data", "")

        await self.channel_layer.group_send(  # type: ignore
            self.room_group_name,
            {"type": "cardRead", "status": status, "cardID": cardID, "data": data},
        )

    async def cardRead(self, event: CardData):
        status = event["status"]
        cardID = event["cardID"]
        cardData = event["data"]

        context: dict = {}

        match status:
            case "Invalid":
                context["error"] = "Read Token Expired! Please Try Again"

            case "Done":
                try:
                    data: dict[str, dict[str, str | list[str]]] = decrypt_data(
                        settings.KEY, cardData
                    )

                    result, header = data.get("data", {}), data.get("header", {})
                    hashedJson = certificateHash(result)

                    view = deconstructSubjects(result, True)

                    context.update(
                        {
                            "data": result,
                            "personal": view.personal_info,
                            "pic": view.image_info,
                            "sem_dict": view.semester_info,
                            "link": hashedJson,
                            "cardID": cardID,
                            **header,
                        }
                    )

                except Exception as e:
                    print(e)
                    context["error"] = "Data cannot be parsed"

            case "Failed":
                context["error"] = "Incorrect Credentials / Data not Found"

            case _:
                context["error"] = DEFAULT_ERROR

        await self.send(
            text_data=render_to_string("Dash/HTMX/read.card.html", context=context),
            close=True,
        )
