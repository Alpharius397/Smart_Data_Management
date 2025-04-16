import datetime
import json
import typing
from django.http import HttpRequest, HttpResponse, JsonResponse
import jwt
from Logs.loggers import DEFAULT_ERROR
from tools.encrypt import getAuthKey
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
    expire_minutes: int
    
    def __init__(self, user: User, expire:datetime.datetime = None, type:str = None, **kawrgs):
        self.username:str = user.username
        self.userID:int = user.id
        self.type = type if(type is not None) else self.__type
        self.expire = (expire if(expire is not None) else timezone.now())
    
    def to_json(self, newToken: bool = False) -> dict[str, str]:
        return {'userID':self.userID, 'username':self.username, 'type':self.type, 'expire': ((self.expire if (not newToken) else timezone.now()) + datetime.timedelta(seconds=self.expire_minutes)).isoformat()}
    
    def getToken(self) -> str:
        return jwt.encode(self.to_json(), settings.JWT_SECRET, settings.JWT_ALGORITHM)
    
    def getNewToken(self) -> str:
        return jwt.encode(self.to_json(newToken=True), settings.JWT_SECRET, settings.JWT_ALGORITHM)
    
    def isCorrectType(self) -> bool:
        return self.type == self.__type
    
    def __str__(self):
        return json.dumps({'userID':self.userID, 'username':self.username, 'type':self.type, 'expire': (self.expire + datetime.timedelta(seconds=self.expire_minutes)).isoformat()})
    
    @staticmethod
    def from_json(classConstruct: 'PayLoad', userID:int, username:str, type:str, expire:str) -> 'PayLoad':
        user:User = User.objects.get(id=userID, username=username)
        return classConstruct(user=user, type=type, expire=datetime.datetime.fromisoformat(expire))  
    
    @staticmethod
    def decodeToken(classConstruct: 'PayLoad', token: str) -> 'PayLoad':
        data:dict[str, str] = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return classConstruct.from_json(classConstruct, **data)

class AccessPayLoad(PayLoad):
    __type: str = 'access'
    expire_minutes = settings.JWT_EXP_DELTA_MINUTES
    
    def __init__(self, user: User, expire:datetime.datetime = None, type:str = None):
        self.username:str = user.username
        self.userID:int = user.id
        self.type = type if(type is not None) else self.__type
        self.expire = (expire if(expire is not None) else timezone.now())


class RefreshPayLoad(PayLoad):
    __type: str = 'refresh'
    expire_minutes = settings.REFRESH_EXP_DELTA_MINUTES
    
    def __init__(self, user: User, expire:datetime.datetime = None, type:str = None):
        self.username:str = user.username
        self.userID:int = user.id
        self.type = type if(type is not None) else self.__type
        self.expire = (expire if(expire is not None) else timezone.now())       

def jwt_required(view_func):
    
    @wraps(view_func)
    def _wrapped_view(request:HttpRequest, *args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        refresh_header = request.headers.get('Refresh', '')
        
        if not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Authorization header missing or malformed'}, status=401)

        if not refresh_header.startswith('Bearer '):
            return JsonResponse({'error': 'Authorization header missing or malformed'}, status=401)

        try:
            access, refresh = auth_header.split(" ")[1], refresh_header.split(" ")[1]
            
            access_payload = AccessPayLoad.decodeToken(AccessPayLoad, access)
            refresh_payload = RefreshPayLoad.decodeToken(RefreshPayLoad, refresh)
            
            if(access_payload.expire<timezone.now() and refresh_payload.expire<timezone.now()):
                raise jwt.ExpiredSignatureError()
            
            if(access_payload.userID != refresh_payload.userID):
                raise jwt.InvalidTokenError()
            
            if(access_payload.expire<timezone.now()):
                print("refreshing")
                access_token = access_payload.getNewToken()
                refresh_token = refresh_payload.getNewToken()
            
            else:
                access_token = access_payload.getToken()
                refresh_token = refresh_payload.getToken()
            
            user = User.objects.get(id=access_payload.userID, username=access_payload.username)
            request.user = user
            request.headers.__setattr__('access', access_token)
            request.headers.__setattr__('refresh', refresh_token)
            return view_func(request, *args, **kwargs)

        except jwt.ExpiredSignatureError:
            return JsonResponse({'error': 'Token expireired'}, status=401)
        
        except jwt.InvalidTokenError:
            return JsonResponse({'error': 'Invalid token'}, status=401)
        
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=401)
        
        except Exception as e:
            print(e)
            return JsonResponse({'error':DEFAULT_ERROR}, status=404)

    return _wrapped_view


def api_key_required(view_func):
    
    @wraps(view_func)
    def _wrapped_view(request:HttpRequest, *args, **kwargs):
        
        try:
            auth_header = request.headers.get('Authorization', '')
        
            if not auth_header.startswith('Bearer '):
                return JsonResponse({'error': 'Authorization header missing or malformed'}, status=401)

            token = auth_header.split(' ')[1]
            if(token and (token==getAuthKey())):
                return view_func(request, *args, **kwargs)
            else:
                return JsonResponse({'error': 'Authorization Token is invalid'}, status=401)
        
        except Exception as e:
            return JsonResponse({'error':DEFAULT_ERROR}, status=404)

    return _wrapped_view