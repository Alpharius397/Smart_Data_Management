from django.shortcuts import render # type: ignore
from django.http import HttpRequest, HttpResponse, JsonResponse # type: ignore
from Main.models import MongoConnection
from django.conf import settings # type: ignore
from tools.typesCauseWhyNot import *
from User.models import get_post_id, get_user_by_id, is_admin, is_manager, get_manager_by_name, get_admin_by_name
from tools.url_auth import *
from tools.encrypt import decrypt_data
from tools.get_image import expand_image
import typing
import re
from Main.models import *
from Logs.loggers import APP_LOG, LogStructure, DEFAULT_ERROR, Task
from tools.token import get_token, hash_token
from django.views.decorators.csrf import csrf_exempt # type: ignore
from tools.encrypt import monthYearHash, jsonHash
from bson.objectid import ObjectId
from bson.errors import InvalidId

VIEW_DATA = {"_id":1,"header.manager":1,"header.uploader":1,"data.header.file_name":1}
READ_TOKEN:str = "read-token"
LOADING:str = "Loading"
DONE:str = "Done"
CARD_DATA:str = "Data"

def get_data(result:list[Document]) -> tuple[bool,list[dict[str, str|list|Any]]]:
    data:list[dict[str, str|list|None]] = []
    empty = bool(result is None)
    
    for i in result:
        
        data.append({
            'id': i._id, 
            'uploader': get_user_by_id(i.header.uploader), 
            'manager': list(map(get_user_by_id,i.header.manager)) ,
            'file_name': i.data.header.file_name
        })

    return empty, data

def get_query(req: HttpRequest) -> dict[str, dict[str, str | list] | str]:
    
    query = req.GET.get('query',None)
    value = req.GET.get('value',None)
    query_dict:dict[str, dict[str, str | list] | str] = {}
    
    if(query and value):
        
        if(query=='uploader'):
            query_dict.update({"header.uploader":{"$in":get_admin_by_name(value)}})
            
        elif(query=='manager'):
            manager_list = get_manager_by_name(value)
            query_list:list[int] = manager_list if (manager_list) else [-1]
            or_dict:dict[str, list[int]] = {"$or": query_list}
            query_dict.update(or_dict) # type: ignore
            
        elif(query=='file_name'):
            query_dict.update({"data.header.file_name":{"$regex":f"/{value}/i"}})
        
        elif(query=='mongo_id'):
            query_dict.update({"_id":ObjectId(value)})
            
    return query_dict

@login_needed()
def dash_board(req: HttpRequest) -> HttpResponse:
    
    if(is_admin(req.user) and is_auth_get(req)):
        get_admin_color(req,req.user)
        return render(req,'Dash/dash/admin.html')

    if(is_manager(req.user) and is_auth_get(req)):
        get_manager_color(req,req.user)
        return render(req,'Dash/dash/manager.html')


@htmx_response
@auth_needed(manager_only=True)
def manager_fetch(req: HttpRequest) -> HttpResponse:
    
    if(is_hx_get(req)):
        
        manage:list[dict[str,str|list]] = []
        conn = MongoConnection().connect()
        error:str = ''
        
        try:
            queryset=get_query(req)
            result:list[Document] = conn.find_all({**queryset,"header.manager":req.user.id},VIEW_DATA)
            flag , manage = get_data(result)
            if(flag and queryset): error='No matching records found!'
        
        except (InvalidId, TypeError):
            error = "Invalid Mongo ID entered"
        
        except Exception as e:            
            APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,user=req.user,exception=e))
            error = DEFAULT_ERROR
            
        finally:
            conn.close()
            
        return render(req,'Dash/HTMX/manager.html',context={'manage':manage,'error':error})

@htmx_response
@auth_needed(admin_only=True)
def admin_upload_fetch(req: HttpRequest) -> HttpResponse:
    
    if(is_hx_get(req)):
        
        admin:list[dict[str,str|list]] = []
        conn = MongoConnection().connect()
        error:str = ''
        
        try:
            queryset=get_query(req)
            result:list[Document] = conn.find_all({**queryset,"header.post":get_post_id(req.user),'header.manager':[]},VIEW_DATA)
            empty, admin = get_data(result)
            if(empty and queryset): error='No matching records found!'
        
        except (InvalidId, TypeError):
            error = "Invalid Mongo ID entered"
        
        except Exception as e:
            APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,user=req.user,exception=e))            
            error = DEFAULT_ERROR
            
        finally:
            conn.close()
            
        return render(req,'Dash/HTMX/admin.uploader.html',context={'upload':admin,'error':error})

@htmx_response
@auth_needed(admin_only=True)
def admin_manage_fetch(req: HttpRequest) -> HttpResponse:
    
    if(is_hx_get(req)):
        
        admin:list[dict[str,str|list]] = []
        error:str = ''
        conn = MongoConnection().connect()
        
        try:
            queryset=get_query(req)
            result:list[Document] = conn.find_all({**queryset,"header.post":get_post_id(req.user),'header.manager':{"$ne":[]}},VIEW_DATA)
            flag, admin = get_data(result)

            if(flag and queryset): error='No matching records found!'
            
        except (InvalidId, TypeError):
            error = "Invalid Mongo ID entered"
        
        except Exception as e:
            APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,user=req.user,exception=e))
            error = DEFAULT_ERROR
            
        finally:
            conn.close()
            
        return render(req,'Dash/HTMX/admin.manager.html',context={'manage':admin,'error':error})


class ReportStructure(typing.NamedTuple):
    profile_img:str
    personal_info:list[str]
    sem_data:dict[str,list[str]]

    @staticmethod
    def get_structure(columns: list[str]) -> 'ReportStructure':
        
        profile_img = r'^Profile_Image$'
        sem_data = r'.+Sem_(\d+)$'
        
        _profile_col = [i for i in columns if re.match(profile_img,i)]
        sem_col = [i for i in columns if re.match(sem_data,i)]
        personal_col = [i for i in columns if((i not in set(_profile_col)) and (i not in set(sem_col)))]
        
        sem_dict:dict[str,list[str]] = {}
        
        profile_col = _profile_col[0] if _profile_col else ''
        
        for i in sem_col:
            _sem:list[str] = re.findall(sem_data,i)
            
            if(_sem):
                sem = _sem[0]
                if(sem not in sem_dict): sem_dict[sem] = list()
                sem_dict[sem].append(i)
                
        return ReportStructure(profile_img=profile_col, personal_info=personal_col, sem_data=sem_dict)

@htmx_response
@auth_needed(manager_only=True)
def read_view(req: HttpRequest)-> HttpResponse:
    
    if(is_hx_get(req)):
        context = {}
            
        try:
            session_data:dict[str, str] = req.session.get(CARD_DATA)
            
            cardData:str = session_data.get("data","")
            cardID:str = session_data.get("cardID","")

            data:dict[str,dict[str,str]] = decrypt_data(settings.KEY,cardData)
            
            result, header = data.get('data',{}), data.get('header',{})
            columns = list(result.keys())
            hashedJson = f"{monthYearHash()}{jsonHash(result)}"
            
            view = ReportStructure.get_structure(columns)
            wid, hei, img = result[view.profile_img].split(":")

            result[view.profile_img] = expand_image(width=int(wid),height=int(hei),img_data=img)

            context.update({'data':result,'personal':view.personal_info,'pic':view.profile_img,'sem_dict':view.sem_data,'link':hashedJson,'cardID':cardID,**header})

        except Exception as e:
            context['error'] = DEFAULT_ERROR
            
        return render(req,'Dash/HTMX/read.card.html',context=context)

@login_needed(manager_only=True)
def read_screen(req: HttpRequest) -> HttpResponse:
    
    Redis = RedisConnection().connect()
    token = get_token()
    req.session[READ_TOKEN] = token
    Redis.set(hash_token(token,req.user.id),{'status':LOADING})
    get_manager_color(req,req.user)
    
    return render(req,'Dash/read.html',context={"path":settings.READ_REGISTRY,"url":req.build_absolute_uri(reverse("Dash:__base__",args=(hash_token(token,req.user.id),)))})

@htmx_response
@auth_needed(manager_only=True)
def check_read(req: HttpRequest) -> HttpResponse:
    if(is_auth_get(req) and is_hx_get(req) and is_manager(req.user)):
        
        token = req.session.get(READ_TOKEN)
        Redis = RedisConnection().connect()
        value = Redis.get(hash_token(token,req.user.id))
        status = value.get('status',None)
        
        if(status==LOADING): # continue to ping as confirmation has not been received
            return HttpResponse(status=404)
        
        elif(status): # Data found. Redirect to Read Screen
            req.session[CARD_DATA] = value
            Redis.unset(hash_token(token,req.user.id))
            return redirect(reverse("Dash:card_read"))
        
        else:            
            return render(req,'Dash/HTMX/read.status.html',context={"error":"Read Token Expired! Please Try Again"})

@csrf_exempt
@api_key_required
def get_read_data(req: HttpRequest, token: str) -> JsonResponse:
    
    json_resp = {"info":"Unauthenticated Request","status":False}
    
    if(req.method=="POST"):
        
        cardID = req.POST.get("cardID", None)
        data = req.POST.get("data",None)

        if(data and cardID):
            Redis = RedisConnection().connect()
            redis_data = Redis.get(token)
            
            if(redis_data.get('status',None)!=LOADING):
                APP_LOG.write_info(LogStructure().set_request(req).set_description(type=Task.INVALID_TOKEN,))
                json_resp['info'] = "Invalid Token"
                return JsonResponse(data=json_resp, status=403, safe=False)
            
            Redis.set(token,{'status':DONE,"data":data, "cardID":cardID})
            Redis.close()
            
            json_resp['info'] = "Data received"
            json_resp['status'] = True
            return JsonResponse(data=json_resp,status=200)
        
        else:
            json_resp['info'] = "Incorrect Credentials / Data not Found"
            return JsonResponse(data=json_resp,status=404)

    return JsonResponse(data=json_resp,status=403)

