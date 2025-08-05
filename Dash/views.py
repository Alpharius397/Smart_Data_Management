from typing import Any, TypedDict
from django.db.models import Q, QuerySet # type: ignore
from django.shortcuts import render  # type: ignore
from django.urls import reverse  # type: ignore
from django.http import HttpRequest  # type: ignore
from Logs.loggers import APP_LOG, LogStructure, LogType
from Main.models import RedisConnection, ReadToken, RedisDataBase
from Main.settings import settingsInterface as settings  # type: ignore
from User.models import (
    RoleType,
    User,
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
    is_hx_put,
    login_needed,
    is_auth_get,
)
from Task.models import TaskTable
from tools.token import get_token, hash_token
from constants import DEFAULT_ERROR, MAX_RECORD, READ_TOKEN
from django.contrib import messages # type: ignore

############ TYPES ############
class FileRecord(TypedDict):
    id: int
    managerCount: int
    semesterCount: int
    createdBy: str 
    file_name: str

class JsonData(TypedDict):
    info: str
    status: bool

class JsonText(TypedDict):
    data: JsonData
    status: int


############ UTILS ############
def get_data(
    result: QuerySet[TaskTable],
) -> tuple[bool, list[FileRecord]]:
    data: list[FileRecord] = []

    for i in result.iterator():
        data.append(
            FileRecord(
                **{
                    "id": i.id,
                    "managerCount": i.assigned.count(),
                    "semesterCount": i.semesterLimit,
                    "createdBy": "" if i.creator is None else i.creator.username,
                    "file_name": i.name,
                }
            )
        )

    return (not result.exists()), data


def get_query(user:User) -> dict[str, Any]:
    query_dict: dict[str, Any] = {}
    
    if is_admin(user):
        query_dict.update({"branch":user.role.belongs})
        
    elif is_manager(user):
        query_dict.update({"branch":user.role.belongs,"assigned__manager": user, "assigned__manager__role__role": RoleType.MANAGER.value})
    
    return query_dict


############ HTTP Request ############
@login_needed()
def dash_board(req: HttpRequest):
    user = get_user(req)
    get_color(req)

    if is_auth_get(req):
        if is_admin(user):
            return render(req, "Dash/HTML/dash/admin.html")
        elif is_manager(user):
            return render(req, "Dash/HTML/dash/manager.html")


@login_needed(manager_only=True)
def read_screen(req: HttpRequest):
    if is_auth_get(req):
        user = get_user(req)
        token = get_token()
        user_read_token = hash_token(token, user.id)

        req.session[READ_TOKEN] = token
        
        return render(
            req,
            "Dash/HTML/read.html",
            context={
                "token": user_read_token,
                "path": settings.READ_REGISTRY,
                "url": req.build_absolute_uri(
                    reverse("Dash:__base__", args=(user_read_token,))
                ),
            },
        )

    return None


############ HTMX Request ############
@htmx_response
@auth_needed()
def task_fetch(req: HttpRequest):
    user = get_user(req)

    if is_hx_get(req):
        next_ = 0
        managers: list[FileRecord] = []

        try:
            queryset = get_query(user)
            start = int(req.GET.get("start", "0"))
            value = req.GET.get("value", "")

            result = TaskTable.objects.filter(
                (Q(id__icontains=value) | Q(name__icontains=value)), **queryset 
            )[start : start + MAX_RECORD]

            flag, managers = get_data(result)

            if value and flag and queryset and start == 0:
                messages.error(req, "No matching records found!")

            elif flag and start == 0:
                if is_admin(user):  messages.error(req, "No Tasks Present!")
                else: messages.error(req, "No Tasks Assigned")

            next_ = start + MAX_RECORD

        except Exception as e:
            APP_LOG.write_info(LogStructure().set_request(req, LogType.EXCEPTION).set_meta(req).set_error(e))
            messages.error(req, DEFAULT_ERROR)

        return render(
            req,
            "Dash/HTMX/task.html",
            context={"managers": managers,"next": next_},
        )

@htmx_response
@auth_needed(manager_only=True)
def read_view(req: HttpRequest):
    user = get_user(req)
    context = {}
    
    if is_hx_put(req):
        read_token = req.session.get(READ_TOKEN, "")
        token = hash_token(read_token, user.id)
        
        context["token"] = token
        context["path"] = settings.READ_REGISTRY
        context["url"] = req.build_absolute_uri(reverse("Card:read", args=(token,)))
        context["ws"] = f"/ws/read/{token}/"
        
        try:
            with RedisConnection(RedisDataBase.CARD_READ_TOKEN) as redis:
                redis.setDict(
                    token,
                    ReadToken(ID=user.id, processing=True, data=""), # type: ignore
                )
        except Exception as e:
            APP_LOG.write_info(LogStructure().set_request(req, LogType.EXCEPTION).set_meta(req).set_error(e))
        
        return render(req, "Dash/HTMX/read/begin.html", context=context)

    elif is_hx_delete(req):
        return render(req, "Dash/HTMX/read/end.html")
