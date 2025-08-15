import typing
from django.contrib import messages  # type: ignore
from django.shortcuts import render  # type: ignore
from django.http import HttpRequest  # type: ignore
from django.db.models import Q  # type: ignore
from Logs.loggers import LogType, APP_LOG, LogStructure, LogMessage
from User.models import get_post_id
from tools.types import NullStr
from tools.url_auth import (
    login_needed,
    auth_needed,
    htmx_response,
    is_hx_get,
    is_auth_get,
    get_user,
    require_http_methods
)
from constants import DEFAULT_ERROR, MAX_RECORD
from Logs.forms import DateForm
from django.db.models.functions import ExtractYear, ExtractMonth, ExtractDay  # type: ignore

COLUMNS_VALUE = ("timestamp", "taskID", "userID", "authLevel", "logType", "action")
COLUMNS_HEADING = (
    "Timestamp",
    "Task ID",
    "User ID",
    "Auth Level",
    "Log Type",
    "Description",
)


@login_needed()
@require_http_methods(['GET'])
def log_board(req: HttpRequest):
    if is_auth_get(req):
        return render(req, "Logs/HTML/dash.html", context={"form": DateForm()})


@auth_needed()
@require_http_methods(['GET'])
@htmx_response
def get_logs(req: HttpRequest):
    if is_hx_get(req):
        _page = req.GET.get("page", "0")
        page = 0
        user = get_user(req)
        f = DateForm(req.GET)
        post = get_post_id(user)

        context: dict[str, str | int | list] = {}
        query = Q(branchID=post["branch"])

        if f.is_valid():
            order: typing.Literal["after", "on", "before"] | str = str(
                f.cleaned_data.get("query", "")
            )
            
            date_log = str(f.cleaned_data.get("date", ""))

            if order and date_log:
                match order:
                    case "after":
                        query = Q(timestamp__gte=date_log)
                    case "on":
                        query = Q(timestamp__icontains=date_log)
                    case "before":
                        query = Q(timestamp__lte=date_log)

        try:
            page = int(_page)
        except:
            page = 0

        context["page"] = page + MAX_RECORD

        try:
            all_records = (
                LogMessage.objects.filter((query) & (Q(branchID=post["branch"])))
                .annotate(
                    day=ExtractDay("timestamp"),
                    month=ExtractMonth("timestamp"),
                    year=ExtractYear("timestamp"),
                )
                .distinct("day", "month", "year")
                .order_by("day", "month", "year")[page : page + MAX_RECORD]
            )

            if all_records.count() == 0:
                if page == 0:
                    messages.error(req, "No Logs Found!")
            else:
                logs = all_records.values_list("year", "month", "day")
                context["logs"] = sorted(logs, reverse=True)

        except Exception as e:
            APP_LOG.write_info(
                LogStructure()
                .set_request(req, LogType.EXCEPTION)
                .set_meta(req)
                .set_error(e)
            )
            messages.error(req, DEFAULT_ERROR)

        return render(req, "Logs/HTMX/log.list.html", context=context)


@login_needed()
@require_http_methods(['GET'])
def single_log(req: HttpRequest, year: int, month: int, day: int):
    if is_auth_get(req):
        context = {"types": [], "columns": [], "day": day, "month": month, "year": year}
        try:
            context["columns"] = COLUMNS_HEADING
            context["types"] = sorted(LogType())
        except Exception as e:
            APP_LOG.write_info(
                LogStructure()
                .set_request(req, LogType.EXCEPTION)
                .set_meta(req)
                .set_error(e)
            )
            context["error"] = DEFAULT_ERROR

        return render(req, "Logs/HTML/read.html", context=context)


@auth_needed()
@require_http_methods(['GET'])
@htmx_response
def search_log(req: HttpRequest, year: int, month: int, day: int):
    if is_hx_get(req):
        user = get_user(req)
        post = get_post_id(user)
        _page = req.GET.get("page", "0")

        post = get_post_id(user)

        try:
            page = int(_page)
        except:
            page = 0

        context = {
            "day": day,
            "month": month,
            "year": year,
            "page": page + MAX_RECORD,
            "logs": [],
        }

        query = (
            Q(branchID=post["branch"])
            & Q(timestamp__day=day)
            & Q(timestamp__month=month)
            & Q(timestamp__year=year)
        )

        search = req.GET.get("search", None)
        column: typing.Literal["userID", "action", "branchID"] | str = str(
            req.GET.get("column", None)
        )
        level: typing.Literal["Unknown", "Student", "Manager", "Admin"] | str = str(
            req.GET.get("level", None)
        )
        logType = req.GET.get("logType", None)

        match column:
            case "userID":
                query &= Q(userID__icontains=search)
            case "branchID":
                query &= Q(taskID__icontains=search)
            case "action":
                query &= Q(action__icontains=search)

        if level:
            query &= Q(authLevel=level)

        if logType:
            value: NullStr = None

            try:
                value = LogType().__getattribute__(logType)
                query &= Q(logType=value)
            except:
                pass

        try:
            all_records = LogMessage.objects.filter((query)).order_by("-timestamp")[
                page : page + MAX_RECORD
            ]
            if all_records.count() == 0:
                if page == 0:
                    messages.error(req, "No Logs Found!")
            else:
                logs = all_records.values_list(*COLUMNS_VALUE)
                context["logs"] = logs

        except Exception as e:
            APP_LOG.write_info(
                LogStructure()
                .set_request(req, LogType.EXCEPTION)
                .set_meta(req)
                .set_error(e)
            )
            messages.error(req, DEFAULT_ERROR)

        return render(req, "Logs/HTMX/log.row.html", context=context)
