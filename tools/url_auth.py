import datetime
import json
import typing
from django.http import HttpRequest, HttpResponse, JsonResponse # type: ignore
import jwt
from Task.models import TaskTable # type: ignore
from constants.constants import DEFAULT_ERROR
from tools.encrypt import authTokenCheck  # type: ignore
from User.models import (  # type: ignore
    Role,
    User,
    get_user,
    is_admin,
    is_authenticated,
    is_manager,
)
from django.db.models import Q # type: ignore
from Main.settings import settingsInterface as settings  # type: ignore
from django.shortcuts import redirect  # type: ignore
from django.urls import reverse  # type: ignore
from University.models import Color  # type: ignore
from functools import wraps  # type: ignore
from django.utils import timezone  # type: ignore


def is_hx_get(req: HttpRequest) -> bool:
    return bool((req.method == "GET") and req.META.get("HTTP_HX_REQUEST"))


def is_auth_get(req: HttpRequest) -> bool:
    return bool(is_authenticated(req.user) and req.method == "GET")


def is_hx_post(req: HttpRequest) -> bool:
    return bool((req.method == "POST") and req.META.get("HTTP_HX_REQUEST"))


def is_auth_post(req: HttpRequest) -> bool:
    return bool(is_authenticated(req.user) and req.method == "POST")


def is_hx_put(req: HttpRequest) -> bool:
    return bool((req.method == "PUT") and req.META.get("HTTP_HX_REQUEST"))


def is_auth_put(req: HttpRequest) -> bool:
    return bool(is_authenticated(req.user) and req.method == "PUT")


def is_hx_delete(req: HttpRequest) -> bool:
    return bool((req.method == "DELETE") and req.META.get("HTTP_HX_REQUEST"))


def is_auth_delete(req: HttpRequest) -> bool:
    return bool(is_authenticated(req.user) and req.method == "DELETE")


def auth_page(req: HttpRequest) -> HttpResponse:
    return redirect(
        reverse(settings.LOGIN_URL) + f"?next={req.path}&alert=Unauthenticated Request!"
    )


def get_color(req: HttpRequest):
    try:
        user: User = get_user(req)
        role: Role = user.role
        color: Color = role.belongs.institute.color
        main_color = color.main_color
        sec_color = color.sec_color
        icon = color.icon.url
        req.session["mainColor"] = main_color
        req.session["secColor"] = sec_color
        req.session["image"] = icon
    except Exception:
        pass

def taskCheck(user: User, id: int):
    try:
        return TaskTable.objects.get(
            Q(id = id) & (Q(branch = user.role.belongs) | Q(assigned__manager__id = user.id))
        )
    except Exception as e:
        print("Task Error: ",e)
        return None

def semesterCheck(user: User, id: int, idx: int):
    try:
        return TaskTable.objects.filter(
            Q(id = id) & Q(data__semester=idx) & (Q(branch = user.role.belongs) | Q(assigned__manager__id = user.id))
        ).distinct()[0]
    except Exception as e:
        print(e)
        return None


def noneCheck(*args: typing.Any) -> bool:
    return not all(args)


class PayLoad:
    __type: str = "Base"
    expire_minutes: int

    def __init__(
        self,
        user: User,
        expire: datetime.datetime | None = None,
        type: str | None = None,
        **kwargs: str | int,
    ):
        self.username: str = user.username
        self.userID: int = user.id
        self.type = type if (type is not None) else self.__type
        self.expire = expire if (expire is not None) else timezone.now()

    def to_json(self, newToken: bool = False) -> dict[str, str | int]:
        return {
            "userID": self.userID,
            "username": self.username,
            "type": self.type,
            "expire": (
                (self.expire if (not newToken) else timezone.now())
                + datetime.timedelta(seconds=self.expire_minutes)
            ).isoformat(),
        }

    def getToken(self) -> str:
        return jwt.encode(self.to_json(), settings.JWT_SECRET, settings.JWT_ALGORITHM)

    def getNewToken(self) -> str:
        return jwt.encode(
            self.to_json(newToken=True), settings.JWT_SECRET, settings.JWT_ALGORITHM
        )

    def isCorrectType(self) -> bool:
        return self.type == self.__type

    def __str__(self):
        return json.dumps(
            {
                "userID": self.userID,
                "username": self.username,
                "type": self.type,
                "expire": (
                    self.expire + datetime.timedelta(minutes=self.expire_minutes)
                ).isoformat(),
            }
        )

    @staticmethod
    def from_json(
        classConstruct: type["PayLoad"],
        userID: int,
        username: str,
        type: str,
        expire: str,
    ) -> "PayLoad":
        user: User = User.objects.get(id=userID, username=username)
        return classConstruct(
            user=user, type=type, expire=datetime.datetime.fromisoformat(expire)
        )

    @staticmethod
    def decodeToken(classConstruct: type["PayLoad"], token: str) -> "PayLoad":
        data: dict[str, str] = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return classConstruct.from_json(classConstruct, **data)  # type: ignore


class AccessPayLoad(PayLoad):
    __type: str = "access"
    expire_minutes = settings.JWT_EXP_DELTA_MINUTES

    def __init__(
        self,
        user: User,
        expire: datetime.datetime | None = None,
        type: str | None = None,
    ):
        self.username: str = user.username
        self.userID: int = user.id
        self.type = type if (type is not None) else self.__type
        self.expire = expire if (expire is not None) else timezone.now()


class RefreshPayLoad(PayLoad):
    __type: str = "refresh"
    expire_minutes = settings.REFRESH_EXP_DELTA_MINUTES

    def __init__(
        self,
        user: User,
        expire: datetime.datetime | None = None,
        type: str | None = None,
    ):
        self.username: str = user.username
        self.userID: int = user.id
        self.type = type if (type is not None) else self.__type
        self.expire = expire if (expire is not None) else timezone.now()


ReqParams = typing.ParamSpec("ReqParams")


def login_needed(manager_only=False, admin_only=False):
    """Wrapper for views that need authenticated users"""

    def wrapper_that_is_wrapped_by_a_wrapper_that_returns_a_wrapper(
        view_func: typing.Callable[..., HttpResponse | None],
    ):
        """*It's the wrap-ception of decorators — a wrap that's wrapped by a wrapper that wraps wrappers.*"""

        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs):
            request.user = get_user(request)
            if is_authenticated(request.user):
                if not (manager_only or admin_only):  # both false
                    return view_func(request, *args, **kwargs) or HttpResponse(
                        status=403
                    )

                if (manager_only and is_manager(request.user)) or (
                    admin_only and is_admin(request.user)
                ):  # one of them is true
                    return view_func(request, *args, **kwargs) or HttpResponse(
                        status=403
                    )

            return auth_page(request)

        return _wrapped_view

    return wrapper_that_is_wrapped_by_a_wrapper_that_returns_a_wrapper


def auth_needed(manager_only=False, admin_only=False):
    """Wrapper for views that need authenticated users (HTMX Version)"""

    def wrapper_that_is_wrapped_by_a_wrapper_that_returns_a_wrapper(
        view_func: typing.Callable[..., HttpResponse | None],
    ):
        """*It's the wrap-ception of decorators — a wrap that's wrapped by a wrapper that wraps wrappers.*"""

        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs):
            request.user = get_user(request)

            if is_authenticated(request.user):
                if (not manager_only) and (not admin_only):
                    return view_func(request, *args, **kwargs) or HttpResponse(
                        status=403
                    )

                if (manager_only and is_manager(request.user)) or (
                    admin_only and is_admin(request.user)
                ):
                    return view_func(request, *args, **kwargs) or HttpResponse(
                        status=403
                    )

            return HttpResponse(status=403)

        return _wrapped_view

    return wrapper_that_is_wrapped_by_a_wrapper_that_returns_a_wrapper


def htmx_response(
    view_func: typing.Callable[..., HttpResponse | None],
):
    """Wrapper for views that are HTMX response"""

    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs):
        if request.META.get("HTTP_HX_REQUEST"):
            request.user = get_user(request)
            return view_func(request, *args, **kwargs) or HttpResponse(status=403)

        return HttpResponse(status=403)

    return _wrapped_view

def task_permission_check(
    view_func: typing.Callable[..., HttpResponse | None],
):
    """Wrapper for views that access tasks"""

    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, id: int, *args, **kwargs):
        user = get_user(request)

        if (task := taskCheck(user, id)) != None:
            request.__setattr__("task", task)
            return view_func(request, id, *args, **kwargs) or HttpResponse(status=403)

        return HttpResponse(status=403)

    return _wrapped_view

def semester_permission_check(
    view_func: typing.Callable[..., HttpResponse | None],
):
    """Wrapper for views that access tasks"""

    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, id: int, idx: int, *args, **kwargs):
        user = get_user(request)
        
        if (task := semesterCheck(user, id, idx)) != None:
            request.__setattr__("task", task)
            return view_func(request, id, idx,*args, **kwargs) or HttpResponse(status=403)

        return HttpResponse(status=403)

    return _wrapped_view

def file_permission_check(
    view_func: typing.Callable[..., HttpResponse | None],
):
    """Wrapper for views that access tasks"""

    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, id: int, *args, **kwargs):
        user = get_user(request)
        
        if taskCheck(user, id):
            return view_func(request, id, *args, **kwargs) or HttpResponse(status=403)

        return HttpResponse(status=403)

    return _wrapped_view

def jwt_required(
    view_func: typing.Callable[..., HttpResponse | None],
):
    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        refresh_header = request.headers.get("Refresh", "")

        if not auth_header.startswith("Bearer "):
            return JsonResponse(
                {"error": "Authorization header missing or malformed"}, status=401
            )

        if not refresh_header.startswith("Bearer "):
            return JsonResponse(
                {"error": "Authorization header missing or malformed"}, status=401
            )

        try:
            access, refresh = auth_header.split(" ")[1], refresh_header.split(" ")[1]

            access_payload = AccessPayLoad.decodeToken(AccessPayLoad, access)
            refresh_payload = RefreshPayLoad.decodeToken(RefreshPayLoad, refresh)

            if (
                access_payload.expire < timezone.now()
                and refresh_payload.expire < timezone.now()
            ):
                raise jwt.ExpiredSignatureError()

            if access_payload.userID != refresh_payload.userID:
                raise jwt.InvalidTokenError()

            if access_payload.expire < timezone.now():
                access_token = access_payload.getNewToken()
                refresh_token = refresh_payload.getNewToken()

            else:
                access_token = access_payload.getToken()
                refresh_token = refresh_payload.getToken()

            user = User.objects.get(
                id=access_payload.userID, username=access_payload.username
            )
            request.user = user
            request.headers.__setattr__("access", access_token)
            request.headers.__setattr__("refresh", refresh_token)
            return view_func(request, *args, **kwargs)

        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token expireired"}, status=401)

        except jwt.InvalidTokenError:
            return JsonResponse({"error": "Invalid token"}, status=401)

        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=401)

        except Exception as e:
            print(e)
            return JsonResponse({"error": DEFAULT_ERROR}, status=404)

    return _wrapped_view


def api_key_required(view_func):
    @wraps(view_func)
    def _wrapped_view(
        request: HttpRequest, *args: ReqParams.args, **kwargs: ReqParams.kwargs
    ):
        try:
            auth_header = request.headers.get("Authorization", "")

            if not auth_header.startswith("Bearer "):
                return JsonResponse(
                    {"error": "Authorization header missing or malformed"}, status=401
                )

            token = auth_header.split(" ")[1]
            if token and (authTokenCheck(token)):
                return view_func(request, *args, **kwargs) or JsonResponse(
                    {"error": "Invalid Request"}, status=403
                )
            else:
                return JsonResponse(
                    {"error": "Authorization Token is invalid"}, status=401
                )

        except Exception as e:
            print(e)
            return JsonResponse({"error": DEFAULT_ERROR}, status=404)

    return _wrapped_view


def getRequestToken(req: HttpRequest):
    return {
        "access": req.headers.__getattribute__("access"),
        "refresh": req.headers.__getattribute__("refresh"),
    }
