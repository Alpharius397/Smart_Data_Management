from typing import TypedDict
from django.db.models import QuerySet, Manager
from django.shortcuts import render  # type: ignore
from django.urls import reverse  # type: ignore
from django.http import HttpRequest, HttpResponse, JsonResponse  # type: ignore
from Main.models import RedisConnection
from django.conf import settings  # type: ignore
from User.models import (
    RoleType,
    get_user,
    is_admin,
    is_manager,
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
from Upload.models import UploadTable
from Logs.loggers import APP_LOG, LogStructure, Task
from tools.token import get_token, hash_token
from django.views.decorators.csrf import csrf_exempt  # type: ignore
from constants.constants import DEFAULT_ERROR, DONE, MAX_RECORD, READ_TOKEN, LOADING
from .sockets import cardReadWebSocket


############ TYPES ############
class FileRecord(TypedDict):
    id: int
    uploader: str
    manager: list[str]
    file_name: str


class JsonData(TypedDict):
    info: str
    status: bool


class JsonText(TypedDict):
    data: JsonData
    status: int


############ UTILS ############
def get_data(
    result: QuerySet[UploadTable],
) -> tuple[bool, list[FileRecord]]:
    data: list[FileRecord] = []

    for i in result:
        assignManager: Manager = i.assigned  # type: ignore
        data.append(
            FileRecord(
                **{
                    "id": i.id,
                    "uploader": i.uploader.username,
                    "manager": [
                        manager[0]
                        for manager in assignManager.distinct("manager").values_list(
                            "manager__username"
                        )
                        if (manager and len(manager) > 0)
                    ],
                    "file_name": i.fileName,
                }
            )
        )

    return (not result.exists()), data


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
            )

        elif query == "file_name":
            query_dict.update({"fileName__icontains": value, "id__icontains": value})

    return query_dict


############ HTTP Request ############
@login_needed()
def dash_board(req: HttpRequest) -> HttpResponse | None:
    user = get_user(req)
    if is_auth_get(req):
        if is_admin(user):
            return render(req, "Dash/dash/admin.html")
        elif is_manager(user):
            return render(req, "Dash/dash/manager.html")

    return None


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

    return None


############ API Request ############
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
@htmx_response
@auth_needed(manager_only=True)
def manager_fetch(req: HttpRequest) -> HttpResponse | None:
    user = get_user(req)

    if is_hx_get(req):
        error: str = ""
        next_ = 0
        managers: list[FileRecord] = []

        try:
            queryset = get_query(req)
            start = int(req.GET.get("start", "0"))

            result = UploadTable.objects.filter(
                **queryset, assigned__isnull=False
            ).distinct("id")[start : start + MAX_RECORD]

            flag, managers = get_data(result)

            if flag and queryset and start == 0:
                error = "No matching records found!"

            elif flag and start == 0:
                error = "No Sheets are assigned"

            next_ = start + MAX_RECORD

        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(type=Task.EXCEPTION, user=user, exception=e)
            )
            error = DEFAULT_ERROR

        return render(
            req,
            "Dash/HTMX/manager.html",
            context={"manager": managers, "error": error, "next": next_},
        )

    return None


@htmx_response
@auth_needed(admin_only=True)
def admin_upload_fetch(req: HttpRequest) -> HttpResponse | None:
    user = get_user(req)

    if is_hx_get(req):
        error: str = ""
        next_ = 0
        uploaders: list[FileRecord] = []

        try:
            queryset = get_query(req)
            start = int(req.GET.get("start", "0"))
            result = UploadTable.objects.filter(
                **queryset,
                assigned__isnull=False,
                assigned__manager__role__role=RoleType.ADMIN,
            ).distinct("id")[start : start + MAX_RECORD]

            flag, uploaders = get_data(result)

            if flag and queryset and start == 0:
                error = "No matching records found!"

            elif flag and start == 0:
                error = "No Sheets are assigned"

            next_ = start + MAX_RECORD

        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(type=Task.EXCEPTION, user=user, exception=e)
            )
            error = DEFAULT_ERROR

        return render(
            req,
            "Dash/HTMX/admin.uploader.html",
            context={"uploader": uploaders, "error": error, "next": next_},
        )

    return None


@htmx_response
@auth_needed(admin_only=True)
def admin_manage_fetch(req: HttpRequest) -> HttpResponse | None:
    user = get_user(req)

    if is_hx_get(req):
        error: str = ""
        next_ = 0
        managers: list[FileRecord] = []

        try:
            queryset = get_query(req)
            start = int(req.GET.get("start", "0"))

            result = UploadTable.objects.filter(
                **queryset,
                assigned__isnull=False,
                assigned__manager__role__role=RoleType.MANAGER,
            ).distinct("id")[start : start + MAX_RECORD]

            flag, managers = get_data(result)

            if flag and queryset and start == 0:
                error = "No matching records found!"

            elif flag and start == 0:
                error = "No Sheets are assigned"

            next_ = start + MAX_RECORD

        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(type=Task.EXCEPTION, user=user, exception=e)
            )
            error = DEFAULT_ERROR

        return render(
            req,
            "Dash/HTMX/admin.manager.html",
            context={"manager": managers, "error": error, "next": next_},
        )

    return None


@csrf_exempt
@htmx_response
@auth_needed(manager_only=True)
def read_view(req: HttpRequest) -> HttpResponse | None:
    user = get_user(req)

    if is_hx_get(req):
        read_token = req.session.get(READ_TOKEN, "")
        token = hash_token(read_token, user.id)
        return render(req, "Dash/HTMX/read/begin.html", context={"token": token})

    elif is_hx_delete(req):
        return render(req, "Dash/HTMX/read/end.html")

    return None
