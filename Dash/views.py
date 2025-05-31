from typing import TypedDict
from django.db.models import QuerySet
from django.shortcuts import render  # type: ignore
from django.urls import reverse  # type: ignore
from django.http import HttpRequest, HttpResponse, JsonResponse  # type: ignore
from Main.models import MongoConnection, RedisConnection, Document
from django.conf import settings  # type: ignore
from tools.typesCauseWhyNot import *
from User.models import (
    get_post_id,
    get_user,
    get_user_by_id,
    is_admin,
    is_manager,
    get_manager_by_name,
    get_admin_by_name,
)
from tools.url_auth import (
    is_hx_get,
    is_hx_delete,
    htmx_response,
    auth_needed,
    get_color,
    login_needed,
    is_auth_get,
    api_key_required,
)
from Dash.errors import ReadFailed, ReadTokenExpired
from Upload.models import UploadTable, DataTable, AssignTable
from Logs.loggers import APP_LOG, LogStructure, Task
from tools.token import get_token, hash_token
from django.views.decorators.csrf import csrf_exempt  # type: ignore
from bson.objectid import ObjectId
from bson.errors import InvalidId
from constants.constants import DEFAULT_ERROR, DONE, MAX_RECORD, READ_TOKEN, LOADING
from .sockets import cardReadWebSocket

############ UTILS ############


############ HTTP Request ############
@login_needed()
def dash_board(req: HttpRequest) -> HttpResponse | None:
    user = get_user(req)
    if is_auth_get(req):
        if is_admin(user):
            return render(req, "Dash/dash/admin.html")
        elif is_manager(user):
            return render(req, "Dash/dash/manager.html")


@login_needed(manager_only=True)
def read_screen(req: HttpRequest) -> HttpResponse | None:
    if is_auth_get(req):
        Redis = RedisConnection().connect()
        token = get_token()
        user = get_user(req)
        user_read_token = hash_token(token, user.id)

        req.session[READ_TOKEN] = token
        Redis.set(
            user_read_token,
            {"status": LOADING, "data": "", "cardID": ""},
        )

        get_color(req)

        return render(
            req,
            "Dash/read.html",
            context={
                "token": user_read_token,
                "path": settings.READ_REGISTRY,
                "url": req.build_absolute_uri(
                    reverse("Dash:__base__", args=(user_read_token,))
                ),
            },
        )


############ API Request ############
class JsonData(TypedDict):
    info: str
    status: bool


class JsonText(TypedDict):
    data: JsonData
    status: int


@csrf_exempt
@api_key_required
def get_read_data(req: HttpRequest, token: str) -> JsonResponse | None:
    json_resp = JsonText(
        data=JsonData(info="Unauthenticated Request", status=False), status=403
    )

    if req.method == "POST":
        cardID = req.POST.get("cardID", "")
        data = req.POST.get("data", "")

        Redis = RedisConnection().connect()
        redis_data = Redis.get(token)

        status = redis_data.get("status", "")
        cardStatus = "Invalid"

        try:
            if status != LOADING:
                raise ReadTokenExpired()

            if not (data and cardID):
                raise ReadFailed()

            cardStatus = DONE

            Redis.set(token, {"status": DONE, "data": data, "cardID": cardID})
            Redis.close()

            json_resp["data"]["info"] = "Data received successfully"
            json_resp["status"] = True

        except Exception as e:
            if isinstance(e, ReadTokenExpired):
                APP_LOG.write_error(
                    LogStructure()
                    .set_request(req)
                    .set_description(
                        type=Task.INVALID_TOKEN,
                    )
                )
                json_resp["data"]["info"] = e.get_error()
                json_resp["status"] = 403

            elif isinstance(e, ReadFailed):
                json_resp["data"]["info"] = e.get_error()
                json_resp["status"] = 400
                cardStatus = "Failed"

            else:
                json_resp["data"]["info"] = DEFAULT_ERROR
                json_resp["status"] = 500
                cardStatus = "Failed"

        cardReadWebSocket(token, cardID, data, cardStatus)

        return JsonResponse(**json_resp, safe=False)

    return None


############ HTMX Request ############
def get_data(
    result: QuerySet[UploadTable],
) -> tuple[bool, list[dict[str, str | list | Any]]]:
    data: list[dict[str, str | list | Any]] = []
    empty = not bool(result)

    for i in result:
        data.append(
            {
                "id": i.id,
                "uploader": i.uploader.username,
                "manager": [
                    manager[0]
                    for manager in i.assigned.distinct("manager").values_list(
                        "manager__username"
                    )
                    if (manager and len(manager) > 0)
                ],
                "file_name": i.fileName,
            }
        )

    return empty, data


def buffered_data(
    conn: MongoConnection,
    conditions: dict,
    column_index: str,
    locked: str,
    status: str,
    issued: str,
    value: str,
    start: int,
    limit: int,
) -> Document | None:
    match_pipeline, search_pipeline, slice_pipeline = (
        MongoTemplate.get_search_buffer_query(
            conditions, column_index, locked, status, issued, value, start, limit
        )
    )
    result: list[Document] = list(
        map(
            Document.get,
            conn.aggregate(match_pipeline, search_pipeline, slice_pipeline),
        )
    )

    if result:
        return result[0]
    return None


def get_query(req: HttpRequest) -> dict[str, str]:
    query = req.GET.get("query", None)
    value = req.GET.get("value", None)
    query_dict: dict[str, str] = {}

    if query and value:
        if query == "uploader":
            query_dict.update(
                {
                    "uploader__username__icontains": value,
                    "uploader__id__icontains": value,
                }
            )
        elif query == "manager":
            query_dict.update(
                {
                    "assigned__manager__username__icontains": value,
                    "assigned__manager__id__icontains": value,
                }
            )  # type: ignore

        elif query == "file_name":
            query_dict.update({"fileName__icontains": value, "id__icontains": value})

    return query_dict


@htmx_response
@auth_needed(manager_only=True)
def manager_fetch(req: HttpRequest) -> HttpResponse:
    user = get_user(req)

    if is_hx_get(req):
        error: str = ""

        start = req.GET.get("start", "0")
        next_ = 0
        try:
            queryset = get_query(req)
            start = int(start)

            result = UploadTable.objects.filter(**queryset)[start : start + MAX_RECORD]

            flag, manage = get_data(result, start)

            if flag and queryset and start == 0:
                error = "No matching records found!"
            elif flag and start == 0:
                error = "No Sheets are assigned"

            next_ = start + MAX_RECORD

        except (InvalidId, TypeError):
            error = "Invalid Mongo ID entered"

        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(type=Task.EXCEPTION, user=req.user, exception=e)
            )
            error = DEFAULT_ERROR

        finally:
            conn.close()

        return render(
            req,
            "Dash/HTMX/manager.html",
            context={"manage": manage, "error": error, "next": next_},
        )


@htmx_response
@auth_needed(admin_only=True)
def admin_upload_fetch(req: HttpRequest) -> HttpResponse:
    if is_hx_get(req):
        upload: list[dict[str, str | list]] = []
        conn = MongoConnection().connect()
        error: str = ""

        start = req.GET.get("start", "0")
        next_ = 0
        try:
            queryset = get_query(req)
            start = int(start)

            project, match_p, skip, limit = MongoTemplate.get_dash_search_buffer_query(
                {
                    **queryset,
                    "header.post": get_post_id(req.user),
                    "header.manager": [],
                },
                VIEW_DATA,
                start,
                MAX_RECORD,
            )
            result: list[Document] = list(
                map(Document.get, conn.aggregate(project, match_p, skip, limit))
            )

            flag, upload = get_data(result, start)

            if flag and queryset and start == 0:
                error = "No matching records found!"

            next_ = start + MAX_RECORD

        except (InvalidId, TypeError):
            error = "Invalid Mongo ID entered"

        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(type=Task.EXCEPTION, user=req.user, exception=e)
            )
            error = DEFAULT_ERROR

        finally:
            conn.close()

        return render(
            req,
            "Dash/HTMX/admin.uploader.html",
            context={"upload": upload, "error": error, "next": next_},
        )


@htmx_response
@auth_needed(admin_only=True)
def admin_manage_fetch(req: HttpRequest) -> HttpResponse:
    if is_hx_get(req):
        manage: list[dict[str, str | list]] = []
        error: str = ""
        conn = MongoConnection().connect()

        start = req.GET.get("start", "0")
        next_ = 0
        try:
            queryset = get_query(req)
            start = int(start)

            project, match_p, skip, limit = MongoTemplate.get_dash_search_buffer_query(
                {
                    **queryset,
                    "header.post": get_post_id(req.user),
                    "header.manager": {"$ne": []},
                },
                VIEW_DATA,
                start,
                MAX_RECORD,
            )
            result: list[Document] = list(
                map(Document.get, conn.aggregate(project, match_p, skip, limit))
            )

            flag, manage = get_data(result, start)

            if flag and queryset and start == 0:
                error = "No matching records found!"

            next_ = start + MAX_RECORD

        except (InvalidId, TypeError):
            error = "Invalid Mongo ID entered"

        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(type=Task.EXCEPTION, user=req.user, exception=e)
            )
            error = DEFAULT_ERROR

        finally:
            conn.close()

        return render(
            req,
            "Dash/HTMX/admin.manager.html",
            context={"manage": manage, "error": error, "next": next_},
        )


@csrf_exempt
@htmx_response
@auth_needed(manager_only=True)
def read_view(req: HttpRequest) -> HttpResponse:
    if is_hx_get(req):
        _token = req.session.get(READ_TOKEN, "")
        token = hash_token(_token, req.user.id)
        return render(req, "Dash/HTMX/read/begin.html", context={"token": token})

    elif is_hx_delete(req):
        return render(req, "Dash/HTMX/read/end.html")


@login_needed(manager_only=True)
def read_screen(req: HttpRequest) -> HttpResponse:
    Redis = RedisConnection().connect()
    token = get_token()
    req.session[READ_TOKEN] = token
    Redis.set(
        hash_token(token, req.user.id),
        {"status": LOADING, "data": None, "cardID": None},
    )
    get_manager_color(req, req.user)

    return render(
        req,
        "Dash/read.html",
        context={
            "token": hash_token(token, req.user.id),
            "path": settings.READ_REGISTRY,
            "url": req.build_absolute_uri(
                reverse("Dash:__base__", args=(hash_token(token, req.user.id),))
            ),
        },
    )
