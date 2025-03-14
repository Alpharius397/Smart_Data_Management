from django.shortcuts import render
from django.http import HttpRequest, HttpResponse, JsonResponse
from Main.models import MongoConnection
from django.conf import settings
from User.models import get_post_id, get_user_by_id, is_authenticated, is_admin, is_manager, get_manager_by_name, get_admin_by_name
from tools.url_auth import *
from tools.encrypt import decrypt_data
from tools.get_image import expand_image
import typing
import re
from Main.models import *
from Logs.loggers import APP_LOG, LogStructure, DEFAULT_ERROR, Task
from tools.token import get_token, hash_token
from django.views.decorators.csrf import csrf_exempt
from io import BytesIO
from base64 import b64encode


VIEW_DATA = {"_id":1,"header.manager":1,"header.uploader":1,"data.header.file_name":1}
READ_TOKEN:str = "read-token"
LOADING:str = "Loading"
DONE:str = "Done"
CARD_DATA:str = "Data"
ERROR_JSON:dict[str, str] = {"info":"Unauthenticated Request","status":False}

def get_data(result:list[dict[str,dict[str,dict|str|list]]]) -> tuple[bool,dict[str,str|list]]:
    data = []
    empty = True
    for i in result:
        if(empty): empty=False
        data.append({'id':i.get('_id'), 'uploader':get_user_by_id(i.get('header',{}).get('uploader')), 'manager':[get_user_by_id(j) for j in i.get('header',{}).get('manager',[])],'file_name':i.get('data',{}).get('header',{}).get('file_name')})

    return empty, data


def dash_board(req: HttpRequest) -> HttpResponse:
    if(not (is_authenticated(req.user))):
        return auth_needed(req)
    
    if(is_admin(req.user) and is_auth_get(req)):
        return render(req,'Dash/dash/admin.html')

    elif(is_manager(req.user) and is_auth_get(req)):
        return render(req,'Dash/dash/manager.html')

    else:
        return HttpResponse(status=403)

def manager_fetch(req: HttpRequest) -> HttpResponse:
    
    if(is_authenticated(req.user) and is_manager(req.user) and is_hx_get(req)):
        
        manage:list[dict[str,str|list]] = []
        conn = MongoConnection().connect()
        error:str = None
        queryset=get_query(req)
        
        try:
            
            result:list[dict[str,dict[str,dict|str|list]]] = conn.find_all({**queryset,"header.manager":req.user.id},VIEW_DATA)
            flag,manage = get_data(result)
            if(flag and queryset): error='No matching records found!'
            
        except Exception as e:            
            APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,user=req.user,exception=e))
            error = DEFAULT_ERROR
            
        finally:
            conn.close()
            
        return render(req,'Dash/HTMX/manager.html',context={'manage':manage,'error':error})
    
    return HttpResponse(status=403)
    
    
def admin_upload_fetch(req: HttpRequest) -> HttpResponse:
    
    if(is_authenticated(req.user) and is_admin(req.user) and is_hx_get(req)):
        
        admin:list[dict[str,str|list]] = []
        conn = MongoConnection().connect()
        error:str = None
        queryset=get_query(req)
        
        try:
            result:list[dict[str,dict[str,dict|str|list]]] = conn.find_all({**queryset,"header.post":get_post_id(req.user),'header.manager':[]},VIEW_DATA)
            flag,admin = get_data(result)
            if(flag and queryset): error='No matching records found!'
            
        except Exception as e:
            APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,user=req.user,exception=e))            
            error = DEFAULT_ERROR
            
        finally:
            conn.close()
            
        return render(req,'Dash/HTMX/admin.uploader.html',context={'upload':admin,'error':error})
    
    return HttpResponse(status=403)
    

def admin_manage_fetch(req: HttpRequest) -> HttpResponse:
    
    if(is_authenticated(req.user) and is_admin(req.user) and is_hx_get(req)):
        
        admin:list[dict[str,str|list]] = []
        error:str = None
        queryset=get_query(req)
        conn = MongoConnection().connect()
        
        try:
            result:list[dict[str,dict[str,dict|str|list]]] = conn.find_all({**queryset,"header.post":get_post_id(req.user),'header.manager':{"$ne":[]}},VIEW_DATA)
            flag, admin = get_data(result)

            if(flag and queryset): error='No matching records found!'

        except Exception as e:
            APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,user=req.user,exception=e))
            error = DEFAULT_ERROR
            
        finally:
            conn.close()
            
        return render(req,'Dash/HTMX/admin.manager.html',context={'manage':admin,'error':error})

    return HttpResponse(status=403)

class ReportStructure(typing.NamedTuple):
    profile_img:str
    personal_info:dict[str,str]
    sem_data:dict[str,dict[str,str]]
    
def read_view(req: HttpRequest)-> HttpResponse:
    
    if(is_auth_get(req) and is_hx_get(req) and is_manager(req.user)):
        context = {}
            
        try:
            # with open(settings.MEDIA_ROOT + '/compress.txt','r') as f:
            #     data:dict[str,dict[str,str]] = decrypt_data(settings.KEY,f.read())
            data:dict[str,dict[str,str]] = decrypt_data(settings.KEY,req.session.get(CARD_DATA))
            
            profile_img = r'^Profile_Image$'
            sem_data = r'.+Sem_(\d+)$'
            
            result, header = data.get('data',{}), data.get('header',{})
            
            columns = result.keys()
            
            profile_col = [i for i in columns if re.match(profile_img,i)]
            sem_col = [i for i in columns if re.match(sem_data,i)]
            personal_col = [i for i in columns if((i not in profile_col) and (i not in sem_col))]
            
            sem_dict:dict[str,list[str]] = {}
            
            profile_col = profile_col[0] if profile_col else None
            
            
            wid, hei, data = result[profile_col].split(":")

            result[profile_col] = expand_image(width=int(wid),height=int(hei),img_data=data)
            for i in sem_col:
                sem:list[str] = re.findall(sem_data,i)
                
                if(sem):
                    sem = sem[0]
                    if(sem not in sem_dict): sem_dict[sem] = list()
                    sem_dict[sem].append(i)

            view = ReportStructure(profile_img=profile_col,personal_info=personal_col,sem_data=sem_dict)
            context.update({'data':result,'personal':view.personal_info,'pic':view.profile_img,'sem_dict':view.sem_data,**header})

        except Exception as e:
            context['error'] = DEFAULT_ERROR
            
        return render(req,'Dash/HTMX/read.card.html',context=context)

    return HttpResponse(status=403)

def read_screen(req: HttpRequest) -> HttpResponse:
    if(not (is_authenticated(req.user) and (is_manager(req.user)))):
        return auth_needed(req)
    
    Redis = RedisConnection().connect()
    token = get_token()
    req.session[READ_TOKEN] = token
    Redis.set(hash_token(token,req.user.id),LOADING)
    
    return render(req,'Dash/read.html',context={"path":settings.READ_REGISTRY,"url":req.build_absolute_uri(reverse("Dash:__base__",args=(hash_token(token,req.user.id),)))})

def get_query(req: HttpRequest) -> dict[str,str]:
    
    query = req.GET.get('query',None)
    value = req.GET.get('value',None)
    query_dict = {}
    
    if(query and value):
        
        if(query=='uploader'):
            query_dict.update({"header.uploader":{"$in":get_admin_by_name(value)}})
        elif(query=='manager'):
            query_dict.update({"$or":[{"header.manager":i} for i in get_manager_by_name(value)]+[{"header.manager":None}]})
        elif(query=='file_name'):
            query_dict.update({"data.header.file_name":{"$regex":f"{value}","$options":"i"}})
            
    return query_dict

    
def check_write(req: HttpRequest) -> HttpResponse:
    if(is_auth_get(req) and is_hx_get(req) and is_manager(req.user)):
        
        token = req.session.get(READ_TOKEN)
        Redis = RedisConnection().connect()
        value = Redis.get(hash_token(token,req.user.id))

        if(value==LOADING): # continue to ping as confirmation has not been received
            return HttpResponse(status=404)
        
        elif(value): # Data found. Redirect to Read Screen
            req.session[CARD_DATA] = value
            Redis.unset(hash_token(token,req.user.id))
            return redirect(reverse("Dash:card_read"))
        
        else:            
            return render(req,'Dash/HTMX/read.status.html',context={"error":"Read Token Expired! Please Try Again"})
        
    return HttpResponse(status=403)

@csrf_exempt
def get_read_data(req: HttpRequest, token: str) -> JsonResponse:
    if(req.method=="POST"):
        api_key = req.POST.get("api_key",None)
        secure_key = req.POST.get("secure_key",None)
        data = req.POST.get("data",None)

        if(data and api_key==settings.API_KEY and secure_key==settings.SECURE_KEY):
            Redis = RedisConnection().connect()
            
            if(Redis.get(token)!=LOADING):
                APP_LOG.write_info(LogStructure().set_request(req).set_description(type=Task.INVALID_TOKEN,))
                return JsonResponse(data={"error":"Invalid Token"}, status=403, safe=False)
            
            Redis.set(token,data)
            Redis.close()
            return JsonResponse(data={"info":"Data received", "status":True},status=200)
        else:
            return JsonResponse(data={"info":"Incorrect Credentials / Data not Found", "status":False},status=404)

    return JsonResponse(data=ERROR_JSON,status=403)

