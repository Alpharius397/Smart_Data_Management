import json # type: ignore
from django.http import HttpRequest, JsonResponse  # type: ignore
from Card.errors import CardIdMissing
from Card.sockets import cardReadWebSocket, cardWriteWebSocket
from Report.errors import DataNotLocked
from Report.views import getProtoReport, getReport
from University.models import Subject
from Task.models import DataTable, TaskTable
from User.models import (
    get_post_id,
    get_user,
    get_post,
)
from tools.encrypt import (
    decrypt_key,
    encrypt_text,
)
from tools.url_auth import (
    is_auth_post,
    api_key_required,
    auth_needed,
    task_permission_check,
    token_check,
    require_http_methods,
)
from Logs.loggers import APP_LOG, LogStructure, LogType
from tools.utils import get_2_value
from django.views.decorators.csrf import csrf_exempt  # type: ignore
from Card.models import Card
from django.db import transaction  # type: ignore
from django.utils import timezone  # type: ignore
from constants import DEFAULT_ERROR
from Main.models import (
    RedisConnection,
    RedisDataBase,
    WriteToken,
)
from Card.types import FetchJson, ConfirmJson, ReadJson


@csrf_exempt
@require_http_methods(["POST"])
@api_key_required  # type: ignore
@token_check(RedisDataBase.CARD_WRITE_TOKEN, close_after=False)
@auth_needed(manager_only=True)
@task_permission_check
def fetch_data(req: HttpRequest, id: int, idx: str, schema: int, token: str):
    user = get_user(req)
    task: TaskTable = req.__getattribute__("task")

    if is_auth_post(req):
        try:
            post = get_post_id(user)

            feed = DataTable.get_complete_feed(task, id, idx)

            if feed.locked is False:
                raise DataNotLocked()

            sem_dict = Subject.getSubjects(schema, post["branch"])  # type: ignore

            post = get_post_id(user)
            sem_dict = Subject.getSubjects(schema, post["branch"])  # type: ignore

            report_data = getReport(sem_dict, task, id, idx, True)

            data = getProtoReport(report_data, get_post_id(user), schema=schema)

            with RedisConnection(RedisDataBase.CARD_WRITE_TOKEN) as redis:
                writeToken = WriteToken(**redis.getDict(token))

                encrypted = encrypt_text(decrypt_key(writeToken["key"]), data)

                card = Card(
                    cardID=1,
                    data=encrypted,
                    done_by=user,
                    decryption_key=writeToken["key"],
                    belongs=user.role.belongs,
                )
                card.save()
                
                APP_LOG.write_info(
                    LogStructure()
                    .set_request(req, LogType.CARD_DATA_FETCH, id, rowID=idx)
                    .set_meta(req)
                )

                return JsonResponse(
                    data=FetchJson(data=encrypted), safe=True, status=200
                )

        except DataNotLocked as f:
            return JsonResponse(
                data=FetchJson(data=f.get_error()), safe=True, status=401
            )

        except Exception as e:
            APP_LOG.write_info(
                LogStructure()
                .set_request(req, LogType.EXCEPTION, id, rowID=idx)
                .set_meta(req)
                .set_error(e)
            )
            return JsonResponse(
                data=FetchJson(data=DEFAULT_ERROR), safe=True, status=500
            )


@csrf_exempt
@require_http_methods(["POST"])
@api_key_required  # type: ignore
@token_check(RedisDataBase.CARD_WRITE_TOKEN)
@auth_needed(manager_only=True)
@task_permission_check
def confirm_view(req: HttpRequest, id: int, idx: str, schema: int, token: str):
    user = get_user(req)
    task: TaskTable = req.__getattribute__("task")
    context: dict = {}
    if is_auth_post(req):
        try:
            with transaction.atomic():
                data = ConfirmJson(**req.POST.dict())  # type: ignore
                post = get_post_id(user)
                sem_dict = Subject.getSubjects(schema, post["branch"])  # type: ignore

                issued = data["status"]
                cardID = data["card"]

                if not cardID:
                    raise CardIdMissing()

                context.update({**get_post(user), **getReport(sem_dict, task, id, idx)})

                DataTable.set_complete_feed(task, id, idx, issued=get_2_value(issued))  # type: ignore

                card, _ = Card.objects.get_or_create(cardID=cardID)

                with RedisConnection(RedisDataBase.CARD_WRITE_TOKEN) as redis:
                    writeToken = WriteToken(**redis.getDict(token))

                    card.data = context  # type: ignore
                    card.last_write = timezone.now()
                    card.done_by = user
                    card.decryption_key = writeToken["key"]

                card.save()
                cardWriteWebSocket(token, data)

                APP_LOG.write_info(
                    LogStructure()
                    .set_request(req, LogType.CARD_DATA_FETCH, id, rowID=idx)
                    .set_meta(req)
                )

                return JsonResponse(
                    data={"status": "Feedback updated successfully"}, status=200
                )

        except CardIdMissing as f:
            data = ConfirmJson(message=f.get_error(), status="false", card="")
            cardWriteWebSocket(token, data)
            return JsonResponse(data={"status": "Feedback updation failed"}, status=401)

        except Exception as e:
            APP_LOG.write_info(
                LogStructure()
                .set_request(req, LogType.EXCEPTION, id, rowID=idx)
                .set_meta(req)
                .set_error(e)
            )
            data = ConfirmJson(message=DEFAULT_ERROR, status="none", card="")
            cardWriteWebSocket(token, data)
            return JsonResponse(data={"status": "Feedback updation failed"}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@api_key_required  # type: ignore
@token_check(RedisDataBase.CARD_READ_TOKEN, False)
@auth_needed(manager_only=True)
def read_view(req: HttpRequest, token: str):
    if is_auth_post(req):
        try:
            data = ReadJson(**req.POST.dict())  # type: ignore

            if not data["card"]:
                raise CardIdMissing()

            cardReadWebSocket(token, data)
            return JsonResponse(
                data={"status": "Card Data received successfully"}, status=200
            )

        except CardIdMissing as f:
            data = ReadJson(message=f.get_error(), status="false", card="", data="")
            cardReadWebSocket(token, data)
            return JsonResponse(data={"status": "Card ID missing"}, status=401)

        except Exception as e:
            APP_LOG.write_info(
                LogStructure()
                .set_request(req, LogType.EXCEPTION)
                .set_meta(req)
                .set_error(e)
            )
            data = ReadJson(message=DEFAULT_ERROR, status="none", card="", data="")
            cardReadWebSocket(token, data)
            return JsonResponse(
                data={"status": "Card Data received failed"}, status=500
            )
