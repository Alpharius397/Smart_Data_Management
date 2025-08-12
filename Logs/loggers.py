from copy import deepcopy
from Task.models import TaskTable
from functools import wraps
import os
import json
import logging
import traceback
from pathlib import Path
from typing import Callable, ParamSpec
from django.utils import timezone  # type: ignore
from django.http import HttpRequest, QueryDict  # type: ignore
from User.models import (
    User,
    get_post_id,
    RoleType,
    get_user,
    is_admin,
    is_manager,
    is_student,
)  # type: ignore
from Main.settings import settingsInterface as settings  # type: ignore
from tools.typesCauseWhyNot import NullInt
from django.db.models import Model  # type: ignore
from django.db.models import CharField, DateTimeField, IntegerField
import typing
import datetime

P = ParamSpec("P")


class LogType:
    """Class Enum, cause yay :)"""

    """ Misc """
    EXCEPTION: str = "Exception Occurred"
    UNAUTH_REQ: str = "Unauthenticated Request"
    INVALID_TOKEN: str = "Invalid Authentication Token"
    WEBSOCKET_FAILED: str = "Websocket Connection Failed"
    WEBSOCKET_RECEIVE: str = "Websocket Connection Received (Not intended)"

    """ Task-Related """
    TASK_CREATE: str = "Task Created"
    TASK_ASSIGN: str = "Assigned Manager to Task"
    TASK_UNASSIGN: str = "Removed Manager from Task"
    TASK_DELETE: str = "Task Deleted"
    TASK_EDIT: str = "Task Edited"

    """ Semester-Related """
    SEM_CREATE: str = "Semester Created"
    SEM_EDIT: str = "Semester Edited"
    SEM_DELETE: str = "Semester Deleted"

    """ GroupBy-Related """
    GROUP_BY: str = "Group-by Column Chosen"

    """ Row-Related """
    DATA_LOCK: str = "Data Row Locked"
    DATA_EDIT: str = "Data Row Edited"
    DATA_UNLOCK: str = "Data Row Unlocked"
    FEED_EDIT: str = "Feedback Provided"

    """ Card-Related """
    CARD_ISSUE: str = "Card Issued"
    CARD_CANCEL: str = "Card Issue Cancelled"
    CARD_DATA_FETCH: str = "Card Data Fetch"

    def __iter__(self) -> typing.Iterator[tuple[str, str]]:
        for attrs in LogType().__dir__():
            if attrs and (attrs[0] == "_"):
                continue

            ref = LogType().__getattribute__(attrs)  # It exists, right?

            yield (attrs, ref)


class BaseLogger:
    def __init__(self, dir_path: Path) -> None:
        self.date_time = timezone.now().strftime("%d.%m.%Y")
        self.__dir_path = dir_path
        self.log = logging.getLogger(self.__class__.__name__)
        BaseLogger.generate_dir(dir_path)

        file_path = os.path.join(dir_path, f"{timezone.now().strftime('%d.%m.%Y')}.log")
        console, file = (
            logging.StreamHandler(),
            logging.FileHandler(file_path, encoding="utf-8"),
        )
        formatter = logging.Formatter(
            "[{asctime}]:[{levelname}]:{message}", style="{", datefmt="%d-%m-%Y %H:%M"
        )
        console.setFormatter(formatter)
        file.setFormatter(formatter)
        self.log.addHandler(console)
        self.log.addHandler(file)
        self.log.setLevel(logging.DEBUG)

    @staticmethod
    def generate_dir(dir_path: Path) -> None:
        os.makedirs(dir_path, exist_ok=True)

    @staticmethod
    def get_error_info(exception: Exception) -> str:
        if isinstance(exception, Exception):
            return f"{exception.__class__.__module__}.{exception.__class__.__name__}: {exception}\n{''.join(traceback.format_tb(exception.__traceback__))}"
        else:
            return "Not an exception"

    @staticmethod
    def change_decorator(func: Callable[P, None]) -> Callable[P, None]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> None:
            if args:
                if isinstance(args[0], BaseLogger):
                    args[0].change_time()

            return func(*args, **kwargs)

        return wrapper

    def change_time(self):
        curr_time = timezone.now().strftime("%d.%m.%Y")
        BaseLogger.generate_dir(self.__dir_path)

        if self.date_time != curr_time:
            file_path = os.path.join(self.__dir_path, f"{curr_time}.log")

            for handler in self.log.handlers[:]:
                if isinstance(handler, logging.FileHandler):
                    self.log.removeHandler(handler)

            file_handler = logging.FileHandler(file_path, encoding="utf-8")
            formatter = logging.Formatter(
                "[{asctime}]:[{levelname}]:{message}",
                style="{",
                datefmt="%d-%m-%Y %H:%M",
            )
            file_handler.setFormatter(formatter)
            self.log.addHandler(file_handler)

            self.date_time = curr_time


class SMTPLogger(BaseLogger):
    @BaseLogger.change_decorator
    def write_error(self, msg: str, where: str = "SMTP") -> None:
        self.log.warning(msg=f"[{where}] {msg}\n", exc_info=True)

    @BaseLogger.change_decorator
    def write_info(self, msg: str, where: str = "SMTP") -> None:
        self.log.info(msg=f"[{where}] {msg}\n")


class RedisLogger(BaseLogger):
    @BaseLogger.change_decorator
    def write_error(self, msg: str, where: str = "REDIS") -> None:
        self.log.warning(msg=f"[{where}] {msg}\n", exc_info=True)

    @BaseLogger.change_decorator
    def write_info(self, msg: str, where: str = "REDIS") -> None:
        self.log.info(msg=f"[{where}] {msg}\n")


class AppLogger(BaseLogger):
    
    @BaseLogger.change_decorator
    def write_info(self, msg: "LogStructure", where: str = "APP") -> None:
        try:
            LogMessage(**msg.get_row()).save()
        except Exception as e:
            temp = deepcopy(msg)
            temp.set_error(e)
            self.log.error(msg=temp.get_log())

        self.log.info(msg=f"[{where}] {msg.get_log()}")

    @BaseLogger.change_decorator
    def write_error(self, msg: "LogStructure") -> None:
        self.log.error(msg=msg.get_log())

APP_LOG, SMTP_LOG, REDIS_LOG = (
    AppLogger(settings.APP_LOG),
    SMTPLogger(settings.SMTP_LOG),
    RedisLogger(settings.DATA_LOG),
)
""" Shared Log Instance """

class DataLog(typing.TypedDict):
    GET: dict[str, typing.Any]
    POST: dict[str, typing.Any]
    PUT: dict[str, typing.Any]
    DELETE: dict[str, typing.Any]
    FILES: dict[str, typing.Any]


class RequestLog(typing.TypedDict):
    branchID: NullInt
    userID: NullInt
    taskID: NullInt
    authLevel: typing.Literal["Unknown", "Student", "Manager", "Admin"]
    timestamp: datetime.datetime
    logType: str
    meta: dict[str, typing.Any]
    url: str
    action: str


class ErrorLog(typing.TypedDict):
    timestamp: datetime.datetime
    error: str
    description: str


class LogStructure:
    META = [
        "REMOTE_ADDR",
        "HTTP_HOST",
        "REQUEST_METHOD",
        "REMOTE_ADDR",
        "REMOTE_HOST",
        "HTTP_USER_AGENT",
    ]
    METHODS: list[typing.Literal["GET", "POST", "PUT", "DELETE"]] = [
        "GET",
        "POST",
        "PUT",
        "DELETE",
    ]

    def __init__(self) -> None:
        self.meta: DataLog | dict = {}
        self.request: RequestLog | dict = {}
        self.error: ErrorLog | dict = {}

    @staticmethod
    def get_data(req: HttpRequest) -> DataLog | dict:
        data: DataLog | dict = {}

        for method in LogStructure.METHODS:
            try:
                attr: QueryDict = req.__getattribute__(method)
                data[method] = attr.dict()
            except AttributeError:
                pass

        try:
            data["FILES"] = {
                name: {
                    "Size": f"{meta.size} bytes",
                    "File Type": meta.content_type,
                    "File Name": meta.name,
                }
                for name, meta in req.FILES.items()
            }
        except Exception:
            pass

        return data

    @staticmethod
    def get_request_data(
        req: HttpRequest, logType: str, taskID: NullInt = None, **kwargs: typing.Any
    ) -> RequestLog | dict:
        data: RequestLog | dict = {}
        user = get_user(req)

        def task_dump(req: HttpRequest):
            try:
                task: TaskTable = req.__getattribute__("task")
                return task.id
            except:
                return None

        data["branchID"] = get_post_id(user)["branch"]
        data["url"] = req.get_full_path()
        data["timestamp"] = timezone.now()
        data["meta"] = {i: req.META.get(i) for i in LogStructure.META}
        data["userID"] = user.id
        data["taskID"] = task_dump(req)
        data["authLevel"] = LogStructure.get_auth(user).value
        data["logType"] = logType
        data["action"] = LogStructure.get_action(req, logType, **kwargs)

        return data

    def set_meta(self, req: HttpRequest):
        self.meta = LogStructure.get_data(req)
        return self

    def set_request(
        self,
        req: HttpRequest,
        logType: str,
        taskId: NullInt = None,
        **kwargs: typing.Any,
    ):
        self.request = LogStructure.get_request_data(req, logType, taskId, **kwargs)
        return self

    def set_error(self, error: Exception):
        self.error["timestamp"] = timezone.now()
        self.error["description"] = "".join(traceback.format_tb(error.__traceback__))
        self.error["error"] = (
            f"{error.__class__.__module__}.{error.__class__.__name__}: {error}"
        )

        return self

    @staticmethod
    def get_auth(user: User | None = None) -> RoleType:
        if user is None:
            return RoleType.UNKNOWN

        if is_admin(user):
            return RoleType.ADMIN  # type: ignore

        elif is_manager(user):
            return RoleType.MANAGER  # type: ignore

        elif is_student(user):
            return RoleType.STUDENT  # type: ignore

        else:
            return RoleType.UNKNOWN  # type: ignore

    @staticmethod
    def get_action(req: HttpRequest, logType: str, **kwargs: typing.Any):
        def user_detail_dump(req: HttpRequest):
            try:
                user = get_user(req)
                return "{0} {1} (ID: {2})".format(
                    LogStructure.get_auth(user).value, user.username, user.id
                )
            except:
                return "{0} {1} (ID: {2})".format(
                    LogStructure.get_auth().value, None, None
                )

        def task_detail_dump(req: HttpRequest):
            try:
                task: TaskTable = req.__getattribute__("task")
                return "Task: {0} (ID: {1})".format(task.id, task.name)
            except:
                return "Task: {0} (ID: {1})".format(None, None)

        def manager_detail_dump(manager: int | str):
            try:
                user = User.objects.get(id=int(manager))
                return "{0} {1} (ID: {2})".format(
                    LogStructure.get_auth(user).value, user.username, user.id
                )
            except:
                return "{0} {1} (ID: {2})".format(
                    LogStructure.get_auth().value, None, None
                )

        match logType:
            case LogType.TASK_CREATE:
                return f"{user_detail_dump(req)} uploaded a new {task_detail_dump(req)}"
            case LogType.TASK_ASSIGN:
                return f"{user_detail_dump(req)} assigned {manager_detail_dump(kwargs.pop('manager', None))} to {task_detail_dump(req)}"
            case LogType.TASK_UNASSIGN:
                return f"{user_detail_dump(req)} unassigned {manager_detail_dump(kwargs.pop('manager', None))} from {task_detail_dump(req)}"
            case LogType.TASK_DELETE:
                return f"{user_detail_dump(req)} deleted the {task_detail_dump(req)}"
            case LogType.TASK_EDIT:
                return (
                    f"{user_detail_dump(req)} re-uploaded the {task_detail_dump(req)}"
                )

            case LogType.GROUP_BY:
                return f"{user_detail_dump(req)} has chosen Column {kwargs.pop('groupBy', None)} for {task_detail_dump(req)}"

            case LogType.SEM_CREATE:
                return f"{user_detail_dump(req)} created the Semester {kwargs.pop('semester', None)} in {task_detail_dump(req)}"
            case LogType.SEM_EDIT:
                return f"{user_detail_dump(req)} edited the Semester {kwargs.pop('semester', None)} in {task_detail_dump(req)}"
            case LogType.SEM_DELETE:
                return f"{user_detail_dump(req)} deleted the Semester {kwargs.pop('semester', None)} in {task_detail_dump(req)}"

            case LogType.DATA_EDIT:
                return f"{user_detail_dump(req)} has edited the Column {kwargs.pop('column', None)}, Data Row ID: {kwargs.pop('rowID', None)} in Semester {kwargs.pop('semester', None)} of {task_detail_dump(req)}"
            case LogType.DATA_LOCK:
                return f"{user_detail_dump(req)} has locked the Data Row ID: {kwargs.pop('rowID', None)} in Semester {kwargs.pop('semester', 'All')} of {task_detail_dump(req)}"
            case LogType.DATA_UNLOCK:
                return f"{user_detail_dump(req)} has unlocked the Data Row ID: {kwargs.pop('rowID', None)} in Semester {kwargs.pop('semester', 'All')} of {task_detail_dump(req)}"
            case LogType.FEED_EDIT:
                return f"{user_detail_dump(req)} has provided feedback on the Data Row ID: {kwargs.pop('rowID', None)} in Semester {kwargs.pop('semester', None)} of {task_detail_dump(req)}"

            case LogType.CARD_ISSUE:
                return f"{user_detail_dump(req)} has issued the card for the Data Row ID: {kwargs.pop('rowID', None)} of {task_detail_dump(req)}"
            case LogType.CARD_CANCEL:
                return f"{user_detail_dump(req)} has cancelled the card for the Data Row ID: {kwargs.pop('rowID', None)} of {task_detail_dump(req)}"
            case LogType.CARD_DATA_FETCH:
                return f"{user_detail_dump(req)} has fetched data for the Data Row ID: {kwargs.pop('rowID', None)} of {task_detail_dump(req)}"

            case LogType.EXCEPTION:
                return f"{user_detail_dump(req)} has encountered a error"
            case LogType.UNAUTH_REQ:
                return f"{user_detail_dump(req)} made an unauthenticated request"
            case LogType.INVALID_TOKEN:
                return f"{user_detail_dump(req)} made a request using an invalid token"
            case LogType.WEBSOCKET_FAILED:
                return f"Websocket connection failed for {user_detail_dump(req)}"
            case LogType.WEBSOCKET_RECEIVE:
                return f"Websocket received data from {user_detail_dump(req)}"

        return None

    def get_log(self):
        meta = deepcopy(self.meta)
        request = deepcopy(self.request)
        error = deepcopy(self.error)

        try:
            if "timestamp" in request:
                request["timestamp"] = request["timestamp"].isoformat()  # type: ignore
            if "timestamp" in error:
                error["timestamp"] = error["timestamp"].isoformat()  # type: ignore
        except:
            pass

        return json.dumps(
            {
                "Meta": meta,
                "Request": request,
                "Error": error,
            }
        )

    def get_row(self):
        return {
            "branchID": self.request.get("branchID"),
            "timestamp": self.request.get("timestamp"),
            "taskID": self.request.get("taskID"),
            "userID": self.request.get("userID"),
            "authLevel": self.request.get("authLevel"),
            "action": self.request.get("action"),
            "logType": self.request.get("logType"),
        }


class LogMessage(Model):
    """Doesn't Contains traceback as this would be visible to users"""

    timestamp = DateTimeField(
        verbose_name="Timestamp of Log", null=False, blank=False, default=timezone.now
    )
    branchID = IntegerField(verbose_name="Branch ID", null=True, blank=True)
    taskID = IntegerField(verbose_name="Task ID", null=True, blank=True)
    userID = IntegerField(verbose_name="User ID", null=True, blank=True)
    authLevel = CharField(
        max_length=255,
        verbose_name="Authentication Level",
        null=False,
        blank=False,
        choices=list(RoleType.getRole()),
    )
    action = CharField(
        max_length=255, verbose_name="Action Performed", null=True, blank=True
    )
    logType = CharField(
        max_length=255,
        verbose_name="Action Performed",
        null=False,
        blank=False,
        choices=list(LogType()),
    )

    def __str__(self):
        return f"{self.timestamp}-{self.userID}-{self.authLevel}-{self.action}"
