from django.shortcuts import render # type: ignore
from django.http import HttpRequest, HttpResponse, JsonResponse # type: ignore
from Main.models import MongoConnection
from django.conf import settings # type: ignore
from tools.typesCauseWhyNot import *
from User.models import get_post_id, get_user_by_id, is_admin, is_manager, get_manager_by_name, get_admin_by_name
from tools.url_auth import *
from Main.models import *
from Logs.loggers import APP_LOG, LogStructure, Task
from tools.token import get_token, hash_token
from django.views.decorators.csrf import csrf_exempt # type: ignore
from bson.objectid import ObjectId
from bson.errors import InvalidId
from constants.constants import *
from .sockets import cardReadWebSocket

def get_data(result:list[Document], index:int = 0) -> tuple[bool,list[dict[str, str|list|Any]]]:
    data:list[dict[str, str|list|Any]] = []
    empty = not bool(result)

    for i in result:
        
        data.append({
            'idx': index + 1,
            'id': i._id, 
            'uploader': get_user_by_id(i.header.uploader), 
            'manager': list(map(get_user_by_id,i.header.manager)) ,
            'file_name': i.data.header.file_name
        })
        
        index+=1

    return empty, data

def buffered_data(conn: MongoConnection, conditions: dict, column_index: str, locked: str, status: str, issued: str, value: str, start: int, limit: int) -> Document | None:
    match_pipeline, search_pipeline, slice_pipeline = MongoTemplate.get_search_buffer_query(conditions, column_index, locked, status, issued, value, start, limit)
    result: list[Document] = list(map(Document.get, conn.aggregate(match_pipeline, search_pipeline, slice_pipeline)))
    
    if(result): return result[0]
    return None

def get_query(req: HttpRequest) -> dict[str, dict[str, str | list] | str | ObjectId ]:
    
    query = req.GET.get('query',None)
    value = req.GET.get('value',None)
    query_dict:dict[str, dict[str, str | list] | str | ObjectId ] = {}
    
    if(query and value):
        
        if(query=='uploader'):
            query_dict.update({"header.uploader":{"$in":get_admin_by_name(value)}})
            
        elif(query=='manager'):
            manager_list = get_manager_by_name(value)
            query_list:list[int] = manager_list if (manager_list) else [-1]
            or_dict:dict[str, list[int]] = {"$or": query_list}
            query_dict.update(or_dict) # type: ignore
            
        elif(query=='file_name'):
            query_dict.update({"data.header.file_name":{ "$regex": f"{value}", "$options": "i",}})
        
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
        
        start = req.GET.get('start', '0')
        next_ = 0
        try:
            queryset=get_query(req)
            start = int(start)
            
            project, match_p, skip, limit = MongoTemplate.get_dash_search_buffer_query({**queryset,"header.manager":req.user.id}, VIEW_DATA, start, MAX_RECORD)
            result: list[Document] = list(map(Document.get,conn.aggregate(project, match_p, skip, limit)))
            
            flag , manage = get_data(result, start)

            if(flag and queryset and start==0): error='No matching records found!'
            elif(flag and start==0): error="No Sheets are assigned"
            
            next_ = start + MAX_RECORD
        
        except (InvalidId, TypeError):
            error = "Invalid Mongo ID entered"
        
        except Exception as e:            
            APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,user=req.user,exception=e))
            error = DEFAULT_ERROR
            
        finally:
            conn.close()
            
        return render(req,'Dash/HTMX/manager.html',context={'manage':manage,'error':error, "next":next_})

@htmx_response
@auth_needed(admin_only=True)
def admin_upload_fetch(req: HttpRequest) -> HttpResponse:
    
    if(is_hx_get(req)):
        
        upload:list[dict[str,str|list]] = []
        conn = MongoConnection().connect()
        error:str = ''
        
        start = req.GET.get('start', '0')
        next_ = 0
        try:
            queryset=get_query(req)
            start = int(start)
            
            project, match_p, skip, limit = MongoTemplate.get_dash_search_buffer_query({**queryset,"header.post":get_post_id(req.user),'header.manager':[]}, VIEW_DATA, start, MAX_RECORD)
            result: list[Document] = list(map(Document.get,conn.aggregate(project, match_p, skip, limit)))

            flag , upload = get_data(result, start)
            
            if(flag and queryset and start==0): error='No matching records found!'

            next_ = start + MAX_RECORD
        
        except (InvalidId, TypeError):
            error = "Invalid Mongo ID entered"
        
        except Exception as e:            
            APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,user=req.user,exception=e))
            error = DEFAULT_ERROR
            
        finally:
            conn.close()
            
        return render(req,'Dash/HTMX/admin.uploader.html',context={'upload':upload,'error':error, "next":next_})

@htmx_response
@auth_needed(admin_only=True)
def admin_manage_fetch(req: HttpRequest) -> HttpResponse:
    
    if(is_hx_get(req)):
        
        manage:list[dict[str,str|list]] = []
        error:str = ''
        conn = MongoConnection().connect()
        
        start = req.GET.get('start', '0')
        next_ = 0
        try:
            queryset=get_query(req)
            start = int(start)
            
            project, match_p, skip, limit = MongoTemplate.get_dash_search_buffer_query({**queryset,"header.post":get_post_id(req.user),'header.manager':{"$ne":[]}}, VIEW_DATA, start, MAX_RECORD)
            result: list[Document] = list(map(Document.get,conn.aggregate(project, match_p, skip, limit)))
            
            flag , manage = get_data(result, start)

            if(flag and queryset and start==0): error='No matching records found!'
            
            next_ = start + MAX_RECORD
            
        except (InvalidId, TypeError):
            error = "Invalid Mongo ID entered"
        
        except Exception as e:
            APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,user=req.user,exception=e))
            error = DEFAULT_ERROR
            
        finally:
            conn.close()
            
        return render(req,'Dash/HTMX/admin.manager.html',context={'manage':manage,'error':error, "next":next_})

@csrf_exempt
@htmx_response
@auth_needed(manager_only=True)
def read_view(req: HttpRequest)-> HttpResponse:
    
    if(is_hx_get(req)):
        _token = req.session.get(READ_TOKEN, '')
        token = hash_token(_token,req.user.id)
        return render(req,'Dash/HTMX/read/begin.html', context={"token":token})

    elif(is_hx_delete(req)):
        return render(req,'Dash/HTMX/read/end.html')

@login_needed(manager_only=True)
def read_screen(req: HttpRequest) -> HttpResponse:
    
    Redis = RedisConnection().connect()
    token = get_token()
    req.session[READ_TOKEN] = token
    Redis.set(hash_token(token,req.user.id),{'status':LOADING,"data":None, "cardID":None})
    get_manager_color(req,req.user)
    
    return render(req,'Dash/read.html',context={"token":hash_token(token,req.user.id),"path":settings.READ_REGISTRY,"url":req.build_absolute_uri(reverse("Dash:__base__",args=(hash_token(token,req.user.id),)))})

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
            status = redis_data.get('status', None)
            
            if((status is None) or (status!=LOADING)):
                APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.INVALID_TOKEN,))
                json_resp['info'] = "Invalid Token"
                cardReadWebSocket(token, status="Invalid", cardID=cardID, data=data)
                return JsonResponse(data=json_resp, status=403, safe=False)
            
            cardReadWebSocket(token, status=DONE, cardID=cardID, data=data)
            
            Redis.set(token,{'status':DONE,"data":data, "cardID":cardID})
            Redis.close()
            
            json_resp['info'] = "Data received"
            json_resp['status'] = True
            return JsonResponse(data=json_resp,status=200)
        
        else:
            json_resp['info'] = "Incorrect Credentials / Data not Found"
            cardReadWebSocket(token, status="Failed", cardID=cardID, data=data)
            
            return JsonResponse(data=json_resp,status=404)

    return JsonResponse(data=json_resp,status=403)