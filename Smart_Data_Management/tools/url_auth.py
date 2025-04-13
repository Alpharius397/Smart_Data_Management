import datetime
import typing
from django.http import HttpRequest, HttpResponse, JsonResponse
import jwt
from Logs.loggers import DEFAULT_ERROR
from User.models import is_authenticated
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from User.models import Admin, Manager
from University.models import Color
from django.contrib.auth.models import User
from functools import wraps
from django.utils import timezone

def is_hx_get(req:HttpRequest) -> bool:
    return bool((req.method=="GET") and req.META.get('HTTP_HX_REQUEST'))

def is_auth_get(req: HttpRequest) -> bool:
    return bool(is_authenticated(req.user) and req.method=='GET')

def is_hx_post(req:HttpRequest) -> bool:
    return bool((req.method=="POST") and req.META.get('HTTP_HX_REQUEST'))

def is_auth_post(req: HttpRequest) -> bool:
    return bool(is_authenticated(req.user) and req.method=='POST')

def is_hx_put(req:HttpRequest) -> bool:
    return bool((req.method=="PUT") and req.META.get('HTTP_HX_REQUEST'))

def is_auth_put(req: HttpRequest) -> bool:
    return bool(is_authenticated(req.user) and req.method=='PUT')

def is_hx_delete(req:HttpRequest) -> bool:
    return bool((req.method=="DELETE") and req.META.get('HTTP_HX_REQUEST'))

def is_auth_delete(req: HttpRequest) -> bool:
    return bool(is_authenticated(req.user) and req.method=='DELETE')

def auth_needed(req:HttpRequest) -> HttpResponse:
    return redirect(reverse(settings.LOGIN_URL) + f"?next={req.path}&alert=Unauthenticated Request!")

def get_admin_color(req: HttpRequest, user: User):
    try:
        admin:Admin = user.admin
        color:Color = admin.belongs.institute.color
        main_color = color.main_color
        sec_color = color.sec_color
        req.session['mainColor'] = main_color
        req.session['secColor'] = sec_color
    except:
        pass
    

def get_manager_color(req: HttpRequest, user: User):
    try:
        admin:Manager = user.manager
        color:Color = admin.belongs.institute.color
        main_color = color.main_color
        sec_color = color.sec_color
        req.session['mainColor'] = main_color
        req.session['secColor'] = sec_color
    except:
        pass

def noneCheck(*args: typing.Any) -> bool:
    return (not all(args))


class PayLoad:
    
    __type: str = None
    expire_second:int
    
    def __init__(self, user: User, type:str = None):
        self.username:str = user.username
        self.userID:int = user.id
        self.type:str = type if(type is not None) else self.__type
    
    def to_json(self) -> dict[str, str]:
        return {'userID':self.userID, 'username':self.username, 'type':self.type, 'exp': timezone.now() + datetime.timedelta(minutes=self.expire_second)}
    
    def getToken(self) -> str:
        return jwt.encode(self.to_json(), settings.JWT_SECRET, settings.JWT_ALGORITHM)
    
    def isCorrectType(self) -> bool:
        return self.type == self.__type
    
    @staticmethod
    def from_json(classConstruct: 'PayLoad', userID:int, username:str, **kwargs) -> 'PayLoad':
        user:User = User.objects.get(id=userID, username=username)
        return classConstruct(user)  
    
    @staticmethod
    def decodeToken(classConstruct: 'PayLoad', token: str) -> 'PayLoad':
        data:dict[str, str] = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return classConstruct.from_json(classConstruct, **data)

class AccessPayLoad(PayLoad):
    __type: str = 'access'
    expire_second = settings.JWT_EXP_DELTA_MINUTES

class RefreshPayLoad(PayLoad):
    __type: str = 'refresh'
    expire_second = settings.REFRESH_EXP_DELTA_MINUTES

def jwt_required(view_func):
    
    @wraps(view_func)
    def _wrapped_view(request:HttpRequest, *args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Authorization header missing or malformed'}, status=401)

        token = auth_header.split(' ')[1]
        try:
            payload = AccessPayLoad.decodeToken(AccessPayLoad, token)
            request.user = payload.user
            return view_func(request, *args, **kwargs)

        except jwt.ExpiredSignatureError:
            return JsonResponse({'error': 'Token expired'}, status=401)
        
        except jwt.InvalidTokenError:
            return JsonResponse({'error': 'Invalid token'}, status=401)
        
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=403)
        
        except Exception as e:
            return JsonResponse({'error':DEFAULT_ERROR}, status=404)

    return _wrapped_view