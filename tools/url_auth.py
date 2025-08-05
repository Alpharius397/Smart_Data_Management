import datetime
import json
import typing
from django.http import HttpRequest, HttpResponse, JsonResponse, QueryDict  # type: ignore
import jwt
from Logs.loggers import APP_LOG, LogStructure, LogType
from Main.models import RedisConnection, WriteToken, ReadToken, RedisDataBase, PdfToken
from Task.models import TaskTable
from constants import ACCESS_TOKEN, DEFAULT_ERROR, EMAIL_KEY, OTP_SIZE
from tools.encrypt import authTokenCheck
from User.models import (
    Role,
    User,
    get_user,
    is_admin,
    is_authenticated,
    is_authenticated_student,
    is_manager,
)
from django.db.models import Q  # type: ignore
from Main.settings import settingsInterface as settings 
from django.shortcuts import redirect  # type: ignore
from django.urls import reverse  # type: ignore
from University.models import Color
from functools import wraps 
from django.utils import timezone # type: ignore
from tools.errors import TokenExpired
from Crypto.Random.random import randint
from asgiref.sync import sync_to_async

REQUEST_PARAMS = typing.ParamSpec("REQUEST_PARAMS")

############ UTILS ############
def getOTP():
    return "".join(map(str, [randint(0, 9) for _ in range(OTP_SIZE)]))

def compareOTP(otp: str, verify: str):
    return (otp == verify)

def is_hx_get(req: HttpRequest) -> bool:
    return bool((req.method == "GET") and req.META.get("HTTP_HX_REQUEST"))

def is_auth_get(req: HttpRequest) -> bool:
    return bool(is_authenticated(get_user(req)) and req.method == "GET")


def is_hx_post(req: HttpRequest) -> bool:
    return bool((req.method == "POST") and req.META.get("HTTP_HX_REQUEST"))


def is_auth_post(req: HttpRequest) -> bool:
    return bool(is_authenticated(get_user(req)) and req.method == "POST")


def is_hx_put(req: HttpRequest) -> bool:
    return bool((req.method == "PUT") and req.META.get("HTTP_HX_REQUEST"))


def is_auth_put(req: HttpRequest) -> bool:
    return bool(is_authenticated(get_user(req)) and req.method == "PUT")


def is_hx_delete(req: HttpRequest) -> bool:
    return bool((req.method == "DELETE") and req.META.get("HTTP_HX_REQUEST"))


def is_auth_delete(req: HttpRequest) -> bool:
    return bool(is_authenticated(get_user(req)) and req.method == "DELETE")


def is_auth_get_student(req: HttpRequest) -> bool:
    return bool(is_authenticated_student(get_user(req)) and req.method == "GET")


def is_auth_post_student(req: HttpRequest) -> bool:
    return bool(is_authenticated_student(get_user(req)) and req.method == "POST")


def is_auth_put_student(req: HttpRequest) -> bool:
    return bool(is_authenticated_student(get_user(req)) and req.method == "PUT")


def is_auth_delete_student(req: HttpRequest) -> bool:
    return bool(is_authenticated_student(get_user(req)) and req.method == "DELETE")


def auth_page(req: HttpRequest) -> HttpResponse:
    return redirect(
        reverse(settings.LOGIN_URL) + f"?next={req.path}&warning=Unauthenticated Request!"
    )


def get_color(req: HttpRequest):
    try:
        user: User = get_user(req)
        role: Role = user.role
        color: Color = role.belongs.institute.color
        main_color = color.main_color
        sec_color = color.sec_color
        instituteIcon = color.instituteIcon.url
        req.session["mainColor"] = main_color
        req.session["secColor"] = sec_color
        req.session["instituteIcon"] = instituteIcon
        
        req.session["university_heading"] = role.belongs.institute.university.name
        req.session["institute_heading"] = role.belongs.institute.name
        req.session["branch_heading"] = role.belongs.name
    except Exception:
        pass


def taskCheck(user: User, id: int):
    try:
        if is_admin(user):
            return TaskTable.objects.get(
                Q(id=id) & Q(branch=user.role.belongs)
            )
            
        elif is_manager(user):
            return TaskTable.objects.get(
                Q(id=id) & Q(assigned__manager__id=user.id)
            )
            
    except Exception as e:
        pass
            
    return None

def semesterCheck(user: User, id: int, idx: int):
    try:
        
        if is_admin(user):
            return TaskTable.objects.filter(
                Q(id=id) & Q(data__semester=idx) & Q(branch=user.role.belongs)
            ).distinct()[0]
            
        elif is_manager(user):
            return TaskTable.objects.filter(
                Q(id=id) & Q(data__semester=idx) & Q(assigned__manager__id=user.id)
            ).distinct()[0]
            
    except Exception as e:
        pass
            
    return None

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
                + datetime.timedelta(minutes=self.expire_minutes)
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

def login_needed(manager_only=False, admin_only=False):
    """Wrapper for views that need authenticated users"""

    def wrapper_that_is_wrapped_by_a_wrapper_that_returns_a_wrapper(
        view_func: typing.Callable[..., HttpResponse | None],
    ):
        """*It's the wrap-ception of decorators — a wrap that's wrapped by a wrapper that wraps wrappers.*"""

        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs):
            get_color(request)
            user = get_user(request)
            if is_authenticated(user):
                if not (manager_only or admin_only):  # both false
                    return view_func(request, *args, **kwargs) or HttpResponse(
                        status=403
                    )

                if (manager_only and is_manager(user)) or (
                    admin_only and is_admin(user)
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
            user = get_user(request)
            
            if (is_authenticated(user)):
                if not (manager_only or admin_only):  # both false
                    return view_func(request, *args, **kwargs) or HttpResponse(
                        status=403
                    )

                if (manager_only and is_manager(user)) or (
                    admin_only and is_admin(user)
                ):  # one of them is true
                    return view_func(request, *args, **kwargs) or HttpResponse(
                        status=403
                    )

            return HttpResponse(status=403)

        return _wrapped_view

    return wrapper_that_is_wrapped_by_a_wrapper_that_returns_a_wrapper

def media_access(view_func: typing.Callable[..., HttpResponse | None],):
    """Wrapper for views that need authenticated users using headers (Headless Chrome fix)"""

    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs):
        
        try:
            token = request.headers.get(ACCESS_TOKEN, "")
            
            with RedisConnection(RedisDataBase.PDF_TOKEN) as redis:
                data: WriteToken | ReadToken | PdfToken = redis.getDict(token) # type: ignore
                
                processing = data.get("processing", None)
                ID = data.get("ID", -1)
                
                if (not isinstance(processing, bool)) or (isinstance(processing, bool) and (processing is not True)):
                    raise TokenExpired()
                
                request.user = User.objects.get(id=ID)
        
        except:
            pass
        
        user = get_user(request)

        if (is_authenticated(user)):
            return view_func(request, *args, **kwargs) or HttpResponse(
                status=403
            )

        return HttpResponse(status=403)

    return _wrapped_view


def aauth_needed(manager_only=False, admin_only=False):
    """Wrapper for views that need authenticated users (HTMX Version)"""

    def wrapper_that_is_wrapped_by_a_wrapper_that_returns_a_wrapper(
        view_func: typing.Callable[..., typing.Awaitable[HttpResponse | None]],
    ):
        """*It's the wrap-ception of decorators — a wrap that's wrapped by a wrapper that wraps wrappers.*"""

        @wraps(view_func)
        async def _wrapped_view(request: HttpRequest, *args, **kwargs):
            
            get_color(request)
            user = get_user(request)
            
            if (await sync_to_async(is_authenticated)(user)):
                if not (manager_only or admin_only):  # both false
                    return await view_func(request, *args, **kwargs) or HttpResponse(
                        status=403
                    )

                if (manager_only and is_manager(user)) or (
                    admin_only and is_admin(user)
                ):  # one of them is true
                    return await view_func(request, *args, **kwargs) or HttpResponse(
                        status=403
                    )

            return HttpResponse(status=403)

        return _wrapped_view

    return wrapper_that_is_wrapped_by_a_wrapper_that_returns_a_wrapper

def student_auth_needed(view_func: typing.Callable[..., HttpResponse | None],):
    """Wrapper for views that need authenticated users (JSON Version)"""

    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs):

        if is_authenticated_student(get_user(request)):
            return view_func(request, *args, **kwargs) or JsonResponse(
                data={"error": DEFAULT_ERROR},
                status=403
            )
        return JsonResponse(data={"error": DEFAULT_ERROR},status=403)

    return _wrapped_view


def htmx_response(
    view_func: typing.Callable[..., HttpResponse | None],
):
    """Wrapper for views that are HTMX response"""

    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs):
        if request.META.get("HTTP_HX_REQUEST"):
            return view_func(request, *args, **kwargs) or HttpResponse(status=403)

        return HttpResponse(status=403)

    return _wrapped_view

def get_user_from_session(
    view_func: typing.Callable[..., HttpResponse | None],
):
    """Wrapper for views that are session auth response"""

    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs):

        try:
            email = request.session.get(EMAIL_KEY, None)
            
            if(email is not None):
                request.user = User.objects.get(email=email)
                
        except Exception as e:
            pass
                
        return view_func(request, *args, **kwargs) or HttpResponse(status=403)

    return _wrapped_view

def set_otp_response(
    view_func: typing.Callable[..., HttpResponse | None],
):
    """Wrapper for views that generates OTP"""

    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs):
        user = get_user(request)
        
        try:
            with RedisConnection(RedisDataBase.OTP_TOKEN) as redis:
                redis.setText(str(user.id), getOTP())
                
            return view_func(request, *args, **kwargs) or HttpResponse(status=403)
        except:
            return HttpResponse(status=403)

    return _wrapped_view

def check_otp_response(
    view_func: typing.Callable[..., HttpResponse | None],
):
    """Wrapper for views that makes uses of OTP (Note: request object gets a `otp` attr that has OTP and `ok` attr that checks if otp is ok)"""

    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs):
        
        request.__setattr__("otp", "Error sending OTP")
        request.__setattr__("ok", False)
        
        user = get_user(request)
        
        try:
            queryDict: QueryDict = request.__getattribute__(str(request.method))
            otp = queryDict.get("OTP", "######")
            
            with RedisConnection(RedisDataBase.OTP_TOKEN) as redis:
                verify = redis.getText(str(user.id))
                request.__setattr__("ok", compareOTP(verify, otp))
                request.__setattr__("otp", verify)
                
        except Exception as e:
            pass
        
        return view_func(request, *args, **kwargs) or HttpResponse(status=403)

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


def async_task_permission_check(
    view_func: typing.Callable[..., typing.Awaitable[HttpResponse | None]],
) -> typing.Callable[..., typing.Awaitable[HttpResponse]]:

    @wraps(view_func)
    async def _wrapped_view(request: HttpRequest, id: int, *args, **kwargs):
        user = get_user(request)

        if (task := await sync_to_async(taskCheck)(user, id)) != None:
            request.__setattr__("task", task)
            return (await view_func(request, id, *args, **kwargs)) or HttpResponse(status=403)

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
            return view_func(request, id, idx, *args, **kwargs) or HttpResponse(
                status=403
            )

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
    view_func: typing.Callable[..., JsonResponse | None],
):
    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs) -> JsonResponse:
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
            return view_func(request, *args, **kwargs) or JsonResponse({"error": DEFAULT_ERROR}, status=403)

        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token expired"}, status=401)

        except jwt.InvalidTokenError:
            return JsonResponse({"error": "Invalid token"}, status=401)

        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=401)

        except Exception as e:
            return JsonResponse({"error": DEFAULT_ERROR}, status=500)

    return _wrapped_view


def api_key_required(view_func: typing.Callable[..., JsonResponse | None]):
    
    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs):
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
            APP_LOG.write_error(LogStructure().set_request(request, LogType.EXCEPTION).set_error(e))
            return JsonResponse({"error": DEFAULT_ERROR}, status=404)

    return _wrapped_view

def pdf_access(view_func: typing.Callable[..., HttpResponse | None]):
    
    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs):
        try:
            auth_header = request.headers.get("Access-PDF", "")

            if not (auth_header == settings.ACCESS_PDF):
                return HttpResponse(status=404)

            return view_func(request, *args, **kwargs) or HttpResponse(status=404)

        except Exception as e:
            return HttpResponse(status=404)
        
    return _wrapped_view

def token_check(database: RedisDataBase, close_after: bool = True):
    """ Checks the token issuer and adds appropriate users for auth """
    
    def __check__(view_func: typing.Callable[..., HttpResponse | None]):
    
        @wraps(view_func)
        def _wrapped_view(
            request: HttpRequest, *args, **kwargs
        ) -> HttpResponse:
            
            try:
                token = kwargs.get("token", "")
                with RedisConnection(database) as redis:
                    data: WriteToken | ReadToken | PdfToken = redis.getDict(token) # type: ignore
                    
                    processing = data.get("processing", None)
                    ID = data.get("ID", -1)
                    
                    if (not isinstance(processing, bool)) or (isinstance(processing, bool) and (processing is not True)):
                        raise TokenExpired()
                    
                    request.user = User.objects.get(id=ID)
                    response = view_func(request, *args, **kwargs) or HttpResponse(status=403)
                    
                    if(close_after): redis.unset(str(token))
                    
                    return response
            
            except User.DoesNotExist:
                return HttpResponse(status=401)
            
            except Exception as e:
                APP_LOG.write_error(LogStructure().set_request(request, LogType.EXCEPTION).set_error(e))
                return HttpResponse(status=404)
        
        return _wrapped_view

    return __check__

def read_body_as_json(view_func: typing.Callable[..., HttpResponse | None]):
    
    @wraps(view_func)
    def _wrapped_view(
        request: HttpRequest, *args, **kwargs
    ):
        
        try:
            if(request.method not in ['GET', 'POST', 'PUT', 'DELETE']):
                raise ValueError("Invalid Request Method")
            request.__setattr__(request.method, json.loads(request.body))
        except Exception as e:
            pass
        
        return view_func(request, *args, **kwargs) or HttpResponse(status=403)
    
    return _wrapped_view

def read_body_as_form(view_func: typing.Callable[..., HttpResponse | None]):
    
    @wraps(view_func)
    def _wrapped_view(
        request: HttpRequest, *args, **kwargs
    ):
        
        try:
            if(request.method not in ['GET', 'POST', 'PUT', 'DELETE']):
                raise ValueError("Invalid Request Method")
            request.__setattr__(request.method, QueryDict(request.body))
        except Exception as e:
            pass
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


class JwtToken(typing.TypedDict):
    access: str
    refresh: str

def getRequestToken(req: HttpRequest):
    return JwtToken(**{
        "access": req.headers.__getattribute__("access"),
        "refresh": req.headers.__getattribute__("refresh"),
    })
