from base64 import b64decode, b64encode
from io import BytesIO
import json
import re
from PIL import Image
from typing import NamedTuple, Any
from django.shortcuts import render
from django.urls import reverse
from django.http import HttpRequest, HttpResponse, JsonResponse
from Main.models import *
from django.conf import settings
from tools.get_image import compress_image
from User.models import Manager, get_post_id, is_admin, is_manager, is_authenticated, get_post, get_user_by_id, get_post_by_ID
import pandas as pd
from bson.objectid import ObjectId
from django.contrib.auth.models import User
from tools.encrypt import encrypt_data, decrypt_data
from Main.templatetags.bad_image import bad_image
from tools.url_auth import is_auth_post, is_hx_get, is_auth_get, is_hx_post, auth_needed, get_admin_color, get_manager_color
from View.forms import VerifyForm
from django.utils import timezone
from Logs.loggers import APP_LOG, LogStructure, DEFAULT_ERROR, Task
from django.views.decorators.csrf import csrf_exempt
from tools.token import get_token, hash_token

MAX_RECORD:int = 5
LOADING:str = "Loading"
DONE:str = "Done"
NONE:str = "None"
FAILED:str = "Failed"
WRITE_TOKEN:str = "write-token"
ERROR_JSON:dict[str, str] = {"info":"Unauthenticated Request","status":False}

def AUTH_VIEW(user: User): return [{"header.uploader":user.id},{"header.manager":user.id},{'header.post':get_post_id(user)}]

class ReportStructure(NamedTuple):
    profile_img:str
    personal_info:dict[str,str]
    sem_data:dict[dict[str,str]]

def report_structure(result:dict[str,Any]) -> ReportStructure:
    
    profile_img = r'^Profile_Image$'
    sem_data = r'.+Sem_(\d+)$'
    other_data = """ Anything not part above is personal """
    
    columns = result.keys()
    
    profile_col = [i for i in columns if re.match(profile_img,i)]
    sem_col = [i for i in columns if re.match(sem_data,i)]
    personal_col = [i for i in columns if((i not in profile_col) and (i not in sem_col))]
    
    sem_dict:dict[str,list[str]] = {}
    
    profile_col = profile_col[0] if profile_col else None
    
    for i in sem_col:
        sem:list[str] = re.findall(sem_data,i)
        
        if(sem):
            sem = sem[0]
            if(sem not in sem_dict): sem_dict[sem] = list()
            sem_dict[sem].append(i)

    return ReportStructure(profile_img=profile_col,personal_info=personal_col,sem_data=sem_dict)

def default_view(req: HttpRequest, id:str) -> HttpResponse:
    
    if(is_hx_get(req)):
        return data_view(req,id)
    
    elif(not (is_authenticated(req.user))):
        return auth_needed(req)
    
    elif(is_admin(req.user)):
        get_admin_color(req,req.user)
        return render(req,'View/table/admin.html',{'id':id})
    
    elif(is_manager(req.user)):
        get_manager_color(req,req.user)
        return render(req,'View/table/manager.html',{'id':id})    
    
    return HttpResponse(status=403)

def search_query(pd_data:pd.DataFrame,column:str,value:str,available_column:list) -> tuple[bool,pd.DataFrame]:
    
    if((column and value) and (column in available_column) and (column in pd_data.columns)):
        pd_data = pd_data[pd_data[column].astype(str).str.contains(value)]

    return (pd_data.empty,pd_data)

def get_context(req: HttpRequest,id:str,conn:MongoConnection, column:str = None, value:str = None, issue:str = None, status:str = None, lock:str = None, page:str = '0') -> dict[str,str]:
    
    
    def state_2_convert(val :str) -> bool | None:
        match(val):
            case "true": return True
            case "false": return False
            case _: return None

    def state_2_check(val: bool, cond: bool) -> bool:
        if(cond is not None):
            return bool(val==cond) or ((not cond) and val is None)
        else:
            return True
    
    def state_3_convert(val :str) -> int:
        match(val):
            case "true": return 0
            case "false": return 1
            case "none": return 2
            case _: return 3

    def state_3_check(val: bool, cond: int) -> bool:
        match(cond):
            case 0: return bool(val==True)
            case 1: return bool(val==False)
            case 2: return bool(val==None)
            case _: return True
    
    result:dict[str,dict[str,dict]] = None
    context = {'id':id}
    search = False
    conn.connect()
    
    try:
        if(is_manager(req.user)):
            result = conn.find_one({"$and":[{"_id":ObjectId(id),"header.manager":req.user.id,"header.post":get_post_id(req.user)}]})
            
        elif(is_admin(req.user)):
            result = conn.find_one({"$and":[{"_id":ObjectId(id),"header.post":get_post_id(req.user)}]})
            
    except Exception as e:
        APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,taskID=id,user=req.user,exception=e))
        context['error'] = DEFAULT_ERROR
        return context
    finally:
        conn.close()
    
    
    if(result is None):
        context['error'] = "Mongo ID %s was not found" % id
        return context
    
    try:
        page = int(page)
        pd_data = pd.DataFrame(result.get('data',{}).get('excel',{}))
        image_idx:list = result.get('data',{}).get('header',{}).get('image_column',[])
        feed_list:list[dict[str,str]] = list(list(result.get('data',{}).get('feed',[])))
        
        verify_idx:list[bool | None] = []
        locked_idx:list[bool | None] = []
        issued_idx:list[bool | None] = []
        v_p, i_p, l_p = set(),set(),set()
        status, issue, lock = state_3_convert(status), state_2_convert(issue), state_2_convert(lock)
        
        for i in feed_list:
            if(state_3_check(i.get('status'),status)):
                v_p.add(i.get('index'))
        
            if(state_2_check(i.get('issued'),issue)):
                i_p.add(i.get('index'))
        
            if(state_2_check(i.get('locked'),lock)):
                l_p.add(i.get('index'))
        
            issued_idx.append(i.get('issued'))
            locked_idx.append(i.get('locked'))
            verify_idx.append(i.get('status'))
        
        available_column = sorted(list(set(pd_data.columns.to_list()) - set([ i for i in image_idx])))
        uploader = get_user_by_id(result.get('header',{}).get('uploader',None))
        manager = [get_user_by_id(i) for i in result.get('header',{}).get('manager',[])]
        
        search, pd_data = search_query(pd_data,column,value,available_column)
        panda_idx = v_p&i_p&l_p
        panda_idx = [i for i,j in enumerate(list(pd_data.index.astype(int))) if(j in panda_idx)][page:page+MAX_RECORD]
        
        pd_data = pd_data.iloc[list(panda_idx)]

    except Exception as e:
        APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,taskID=id,user=req.user,exception=e))
        context['error'] = DEFAULT_ERROR
        return context
    
    if(search):
        context['error'] = "No matching records found"
    else:
        context.update({'column':pd_data.columns,'upload':uploader,'manage':manager,'result':pd_data.iterrows(),'image':image_idx,'verify':verify_idx,'issued':issued_idx,'available':available_column,'start':page,'max_record':page+MAX_RECORD,'locked':locked_idx})
    return context


def data_view(req: HttpRequest,id) -> HttpResponse:

    if(is_auth_get(req)):
    
        conn = MongoConnection().connect()
        context = get_context(req, id, conn)
        conn.close()
        context.update({"admin":is_admin(req.user)})
        return render(req,'View/HTMX/page.html',context=context)
    
    else:
        return auth_needed(req)


def assign_form(req:HttpRequest, id:str) -> HttpResponse:
    
    if(is_authenticated(req.user) and is_hx_get(req) and is_admin(req.user)):
        
        conn = MongoConnection().connect()
        result:dict[str,dict[str,dict]] = None
        context = {'id':id}
        
        try:
            result = conn.find_one({"$and":[{"_id":ObjectId(id),"header.post":get_post_id(req.user)}]},{"header.uploader":1,"header.manager":1})
            
        except Exception as e:            
            APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,taskID=id,user=req.user,exception=e))
            context['error'] = DEFAULT_ERROR
            conn.close()
            
            return render(req,'View/HTMX/form.html',context=context)

        try:
            user:User = req.user
            uploader = get_user_by_id(result.get('header',{}).get('uploader',None))
            manager = {i:get_user_by_id(i) for i in result.get('header',{}).get('manager',[])}
            all_manager = {i.get('user_id'):get_user_by_id(i.get('user_id')) for i in Manager.objects.filter(belongs__id=user.admin.belongs.id).exclude(user__id__in=list(manager.keys())).values()}
            context.update({'upload':uploader,'manage':manager,'option':all_manager})
            
        except Exception as e:
            APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,taskID=id,user=req.user,exception=e))
            context['error'] = DEFAULT_ERROR

        finally:
            conn.close()
            
        return render(req,'View/HTMX/form.html',context=context)
    
    
    elif(is_authenticated(req.user) and is_hx_post(req) and is_admin(req.user)):
        
        conn = MongoConnection().connect()
        result:dict[str,dict[str,dict]] = None
        file_name:str = None
        context = {'id':id}

        user:str = req.POST.get('user',None)
        to_do = req.POST.get('to_do',None)

        match to_do:
            case "assign": to_do = True
            case "delete": to_do = False
            case _: to_do = None
        
        if(to_do is None or user is None):
            context['error'] = "User not found"
            return render(req,'View/HTMX/message.html',context=context)
            
        try:
            result = conn.find_one({"$and":[{"_id":ObjectId(id),"header.post":get_post_id(req.user)}]},{"header.manager":1,"data.header.file_name":1})
            
        except Exception as e:
            APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,taskID=id,user=req.user,exception=e))
            context['error'] = DEFAULT_ERROR
            return render(req,'View/HTMX/message.html',context=context)
            
        
        try:
            manager = [i for i in result.get('header',{}).get('manager',[])]
            file_name = result.get("data",{}).get("header",{}).get("file_name",None)
            all_manager = [get_user_by_id(i.get('user_id')) for i in Manager.objects.filter(belongs__id=req.user.admin.belongs.id).exclude(user__id__in=manager).values()]
            _manage = Manager.objects.get(user__id=user)
        except Exception as e:
            APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,taskID=id,user=req.user,exception=e))
            context['error'] = DEFAULT_ERROR
            return render(req,'View/HTMX/message.html',context=context)
        
        try:
            if(to_do):
                
                if(_manage.user.id in manager):
                    context['msg'] = "Manager %(manage)s is already assigned to task ID %(id)s" % {'manage':_manage.user.username,'id':id}
                else:
                    manager.append(_manage.user.id)
                    manager = list(set(manager))
                    
                    conn.update_one({"$and":[{"_id":ObjectId(id),"header.post":get_post_id(req.user)}]},{"$set":{'header.manager':manager}})
                    APP_LOG.write_info(LogStructure().set_request(req).set_description(type=Task.TASK_ASSIGN,taskID=id,manager=_manage.user,fileName=file_name,user=req.user))
                    context['msg'] = "Add Manager %(manage)s to task ID %(id)s" % {'manage':_manage.user.username,'id':id}
            else:
                
                if(_manage.user.id not in manager):
                    context['msg'] = "Manager %(manage)s was not assigned to task ID %(id)s" % {'manage':_manage.user.username,'id':id}
                else:
                    manager.remove(_manage.user.id)
                    manager = list(set(manager))
                    
                    conn.update_one({"$and":[{"_id":ObjectId(id),"header.post":get_post_id(req.user)}]},{"$set":{'header.manager':manager}})
                    APP_LOG.write_info(LogStructure().set_request(req).set_description(type=Task.TASK_UNASSIGN,taskID=id,manager=_manage.user,fileName=file_name,user=req.user))
                    context['msg'] = "Removed Manager %(manage)s from task ID %(id)s" % {'manage':_manage.user.username,'id':id}

        except Exception as e:
            APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,taskID=id,user=req.user,exception=e))
            context['error'] = DEFAULT_ERROR
            return render(req,'View/HTMX/message.html',context=context)
        
        finally:
            conn.close()
            
        return render(req,'View/HTMX/message.html',context=context)
            

    return HttpResponse(status=403)


def table_query(req: HttpRequest, id:str) -> HttpResponse:
    
    if((is_authenticated(req.user)) and is_hx_get(req)):
        
        conn = MongoConnection().connect()
        column = req.GET.get('column',None)
        value = req.GET.get('search',None)
        issue = req.GET.get('issue',None)
        status = req.GET.get('status',None)
        lock = req.GET.get('lock',None)
        page = req.GET.get('page','0')
        
        context = get_context(req,id,conn,column,value,issue,status,lock,page)
        context.update({"admin":is_admin(req.user)})
        conn.close()
        return render(req,'View/HTMX/table.html',context=context)
    
    return HttpResponse(status=403)

def row_view(req: HttpRequest, id:str) -> HttpResponse:
    
    if((is_authenticated(req.user)) and is_hx_get(req)):
        
        conn = MongoConnection().connect()
        column = req.GET.get('column',None)
        value = req.GET.get('search',None)
        issue = req.GET.get('issue',None)
        status = req.GET.get('status',None)
        lock = req.GET.get('lock',None)
        page = req.GET.get('page','0')
        
        context = get_context(req,id,conn,column,value,issue,status,lock,page)
        context.update({"admin":is_admin(req.user)})
        conn.close()
        
        return render(req,'View/HTMX/row.html',context=context)
    
    return HttpResponse(status=403)
    

def quick_query(req: HttpRequest, id:str):
    if((is_authenticated(req.user)) and is_hx_get(req)):
    
        conn = MongoConnection().connect()
        column = req.GET.get('column',None)
        search = req.GET.get('search','')
        context = {'option':[]}
        
        try:
            result:dict[str,dict[str,dict]] = conn.find_one({"$and":[{"_id":ObjectId(id),"$or":AUTH_VIEW(req.user)}]},{"data.excel":1})
            pd_data = pd.DataFrame(result.get('data',{}).get('excel',{}))
            
            if(column in pd_data.columns):
                pd_data = pd_data[pd_data[column].str.contains(search)][column].to_numpy()
                context['option'] = [i for i in sorted(set(pd_data))[:5]]    
                
        except Exception as e:
            APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,taskID=id,user=req.user,exception=e))
            context['error'] = DEFAULT_ERROR
            
        return render(req,'View/HTMX/suggests.html',context=context)
    
    
def index_view(req: HttpRequest, id:str, idx:int) -> HttpResponse:
    
    if(is_hx_get(req)):
        return report_view(req,id,idx)
    
    elif(is_hx_post(req)):
        return report_view(req,id,idx)
    
    elif(not (is_authenticated(req.user))):
        return auth_needed(req)
    
    else:
        get_admin_color(req,req.user)
        get_manager_color(req,req.user)
        return render(req,'View/single.html',{'id':id,'idx':idx,'manage':is_manager(req.user)})

    
def report_view(req: HttpRequest, id:str, idx:int) ->HttpResponse:

    if(is_authenticated(req.user) and is_hx_get(req)):
        
        conn = MongoConnection().connect()
        context = {'id':id,'idx':idx}
        
        try:
            result:dict[str,dict[str,dict]] = conn.find_one({"$and":[{"_id":ObjectId(id),"$or":AUTH_VIEW(req.user)}]},{"header":1,"data.header":1,"data.feed":1,"data.excel":1})
            meta_data:dict = result.get('data',{}).get('feed',[])[idx]
            pd_data = pd.DataFrame(result.get('data',{}).get('excel',{})).iloc[idx]
        except Exception as e:
            APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,taskID=id,index=idx,user=req.user,exception=e))
            context['error'] = DEFAULT_ERROR
            return render(req,'View/HTMX/report.html',context=context)
        
        finally:
            conn.close()
            
        if(pd_data.empty or (not meta_data)):
            context['error'] = "Mongo ID %s and index %s not found!" % id,idx
            return render(req,'View/HTMX/report.html',context=context)
        
        else:
            pd_data = pd_data.to_dict()
            
            report = report_structure(pd_data)
            
            context.update({'data':pd_data,'personal':report.personal_info,'pic':report.profile_img,'sem_dict':report.sem_data,**get_post(req.user),**meta_data})
            
        return render(req,'View/HTMX/report.html',context=context)
    
    return HttpResponse(status=403)
    
def feed_view(req: HttpRequest, id:str, idx:int) ->HttpResponse:

    if(is_authenticated(req.user) and is_hx_post(req) and is_manager(req.user)):
        
        conn = MongoConnection().connect()
        context = {'id':id,'idx':idx}
        
        f = VerifyForm(req.POST)
        
        if(f.is_valid()):
            status, feed = f.cleaned_data.get("status"), f.cleaned_data.get("feedback") 
            
            if(status=='True'):
                status = True
            elif(status=='False'):
                status = False
            else:
                status = None
                
            try:
                column = f"data.feed"
                index_col = f"{column}.index"
                status_col = f"{column}.{idx}.status"
                feed_col = f"{column}.{idx}.feed"
                success = conn.update_one({"_id":ObjectId(id),"$or":AUTH_VIEW(req.user),index_col:idx},{"$set":{status_col:status,feed_col:feed}})
                file_name = conn.find_one({"_id":ObjectId(id)},{"data.header.file_name":1}).get("data",{}).get("header",{}).get("file_name",None)

                if(success):
                    context['msg'] = "Status Updated!"
                    APP_LOG.write_info(LogStructure().set_request(req).set_description(type=Task.FEED_EDIT,taskID=id,index=idx,user=req.user,fileName=file_name))
                else:
                    context['error'] = "Mongo ID %s not found" % id
                    
            except Exception as e:
                APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,taskID=id,index=idx,user=req.user,exception=e))
                context['error'] = DEFAULT_ERROR
                
            finally:
                conn.close()    
        else:
            context['error'] = f.errors.as_text()
            
        return render(req,'View/HTMX/message.html',context=context)
    
    elif(is_authenticated(req.user) and is_hx_get(req) and is_manager(req.user)):
        conn = MongoConnection().connect()
        context = {'id':id,'idx':idx}
        
        try:
            result:dict[str,dict[str,dict]] = conn.find_one({"$and":[{"_id":ObjectId(id),"header.manager":req.user.id,"header.post":get_post_id(req.user)}]},{"data.feed":1,"header.manager":1})
            meta_data:list[dict] = result.get('data',{}).get('feed',[])[idx]
            manager:list[str] = [get_user_by_id(i) for i in result.get('header',{}).get('manager',[])]
            context.update({**meta_data,'manager':manager})

        except Exception as e:
            context['error'] = DEFAULT_ERROR
        finally:
            conn.close()
        
        context.update({'form':VerifyForm(data={'status':(lambda x: 'True' if x else ('False') if x is not None else ('None'))(context.get('status','None')),'feed':context.get('feed','')})})
        return render(req,'View/single/manager.html',context=context)
    
    elif(is_authenticated(req.user) and is_hx_get(req)):

        conn = MongoConnection().connect()
        context = {'id':id,'idx':idx}
        
        try:
            result:dict[str,dict[str,dict]] = conn.find_one({"$and":[{"_id":ObjectId(id),"$or":AUTH_VIEW(req.user)}]},{"data.feed":1,"header.manager":1})
            meta_data:dict = result.get('data',{}).get('feed',[])[idx]
            manager:list[str] = [get_user_by_id(i) for i in result.get('header',{}).get('manager',[])]
            context.update({**meta_data,'manager':manager})
            
        except Exception as e:
            APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,taskID=id,user=req.user,exception=e))
            context['error'] = DEFAULT_ERROR
            
        finally:
            conn.close()
            
        return render(req,'View/single/admin.html',context=context)
        
    return HttpResponse(status=403)
            
def compress_view(req: HttpRequest, id:str, idx:int) -> HttpResponse:
    
    if(is_authenticated(req.user) and is_manager(req.user)):
        
        if(is_hx_get(req)):
            
            conn = MongoConnection().connect()
            
            context = {'id':id,'idx':idx}
            try:
                result:dict[str,dict[str,dict]] = conn.find_one({"$and":[{"_id":ObjectId(id),"$or":AUTH_VIEW(req.user)}]})
                meta_data:dict = result.get('data',{}).get('feed',[])[idx]
                context.update({**meta_data})
            except Exception as e:
                APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,taskID=id,index=idx,user=req.user,exception=e))
                context['error'] = DEFAULT_ERROR
                return render(req,'View/single/manager_form.html',context=context)

            return render(req,'View/single/manager_form.html',context=context)
        
        elif(is_hx_post(req)):
            to_do = req.POST.get("to_do")
            
            conn = MongoConnection().connect()
            
            context = {'id':id,'idx':idx}
            timestamp = None
            locked = None

            match(to_do):
                case "issue": locked = True
                case "cancel": locked = False
                case _: locked = False
                
            if(locked):
                timestamp = timezone.now().isoformat()
            
            try:
                time_issue = f"data.feed.{idx}.time_of_lock"
                locked_col = f"data.feed.{idx}.locked"
                res = conn.update_one({"_id":ObjectId(id)},{"$set":{time_issue:timestamp,locked_col:locked}})
                file_name = conn.find_one({"_id":ObjectId(id)},{"data.header.file_name":1}).get("data",{}).get("header",{}).get("file_name",None)

                if(res and locked): 
                    APP_LOG.write_info(LogStructure().set_request(req).set_description(type=Task.DATA_LOCK,taskID=id,index=idx,user=req.user,fileName=file_name))
                    context['msg'] = "Card Issued"
                
                elif(res): 
                    APP_LOG.write_info(LogStructure().set_request(req).set_description(type=Task.DATA_UNLOCK,taskID=id,index=idx,user=req.user,fileName=file_name))
                    context['msg'] = "Card Cancelled"
                    
                else: context['error'] = "Data updation failed"
            
            except Exception as e:
                APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,taskID=id,index=idx,user=req.user,exception=e))
                context['error'] = DEFAULT_ERROR
                return render(req,'View/HTMX/message.html',context=context)
            
            finally:
                conn.close()
            
            return render(req,'View/HTMX/message.html',context=context)
        
    return HttpResponse(status=403)
            
def compress_data(result:dict[str,dict[str,dict]], idx:int, local_write:bool = True, buffer_out:bool = True) -> BytesIO | dict:
    
    pd_data = pd.DataFrame(result.get('data',{}).get('excel',{}))
    image_idx:list = result.get('data',{}).get('header',{}).get('image_column',[])
    data = pd_data.iloc[idx].to_dict()
    header = get_post_by_ID(**result.get('header',{}).get("post",{}))
    
    for i in image_idx:
        img_data = data[i]
        raw_img = img_data.split(':')
    
        try:
            _, _, img = raw_img
        except:
            img = bad_image

        img = compress_image(BytesIO(b64decode(img)))
        data[i] = img
        
    if(local_write):
        with open(settings.MEDIA_ROOT + '/compress.txt','w') as f:
            f.write(encrypt_data(settings.KEY,{"data":data,"header":header}))
            
        with open(settings.MEDIA_ROOT + '/decompress.txt','w') as f:
            f.write(json.dumps(decrypt_data(settings.KEY,encrypt_data(settings.KEY,{"data":data,"header":header}))))
    
    buffer = BytesIO()
    buffer.write(encrypt_data(settings.KEY,{"data":data,"header":header}).encode())
    buffer.seek(0)
    
    return buffer if(buffer_out) else data       

def card_view(req: HttpRequest, id:str, idx:int) -> HttpResponse:
    
    if(is_auth_get(req) and is_hx_get(req) and is_manager(req.user)):
        
        req.session[WRITE_TOKEN] = get_token()     
        hashToken = hash_token(req.session.get(WRITE_TOKEN), req.user.id)
        api_endpoint = f"{req.build_absolute_uri(reverse("View:__base__", args=(id,idx,hashToken)))}"
        
        return render(req,"View/HTMX/exe/end.html",context={"id":id,"idx":idx,"data":api_endpoint,"path":settings.WRITE_REGISTRY}) # end write op

    if(is_auth_post(req) and is_hx_post(req) and is_manager(req.user)):
        Redis = RedisConnection().connect()
        hashToken = hash_token(req.session.get(WRITE_TOKEN), req.user.id)
        Redis.set(hashToken, LOADING)
        
        return render(req,"View/HTMX/exe/begin.html",context={"id":id,"idx":idx}) # begin write op

    return HttpResponse(status=403)

def check_write(req: HttpRequest) -> HttpResponse:
    if(is_auth_get(req) and is_hx_get(req) and is_manager(req.user)):
        
        token = req.session.get(WRITE_TOKEN)
        Redis = RedisConnection().connect().get(hash_token(token,req.user.id))

        if(Redis==LOADING): # continue to ping as confirmation has not been received
            return HttpResponse(status=404)
        elif(Redis==DONE):
            return render(req,'View/HTMX/exe/status.html',context={"status":"Data written to card successfully"})
        elif(Redis==FAILED):
            return render(req,'View/HTMX/exe/status.html',context={"status":"Data write was unsuccessfully"})
        else:   
            return render(req,'View/HTMX/exe/status.html',context={"status":"Write Token Expired! Please Try Again"})
        
    return HttpResponse(status=403)


def edit_form(req: HttpRequest, id: str, idx:int) -> HttpResponse:
    if(is_hx_get(req) and is_authenticated(req.user) and is_admin(req.user)):
        column = req.GET.get('column',None)
        value = req.GET.get("value","")
        
        return render(req,'View/HTMX/edit_form/edit_form.html',context={"id":id,"column":column,"idx":idx,"value":value,})
    
    elif (is_hx_post(req) and is_authenticated(req.user) and is_admin(req.user)):
        column = req.POST.get('column',None)
        value = req.POST.get("value",)
        j = req.POST.get("j","")
        old = req.POST.get("old","")
        
        conn = MongoConnection().connect()

        context = {"id":id,"idx":idx,"value":value,"admin":True,"column":column}
        try:
            column_name = f"data.excel.{column}.{idx}"
            feed_idx = f"data.feed.{idx}.index"
            lock_idx = f"data.feed.{idx}.locked"
            
            res = conn.update_one({"_id":ObjectId(id),feed_idx:idx,lock_idx:{"$ne":True}},{"$set":{column_name:value}})
            file_name = conn.find_one({"_id":ObjectId(id)},{"data.header.file_name":1}).get("data",{}).get("header",{}).get("file_name",None)
            
            if(res):
                APP_LOG.write_info(LogStructure().set_request(req).set_description(type=Task.DATA_EDIT,taskID=id,index=idx,column=column,user=req.user,fileName=file_name))
            else:
                context['lock'] = True
                context['error'] = "Cannot Edit this index as its locked"
                
        except Exception as e:
            APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,taskID=id,index=idx,user=req.user,exception=e))
            context['error'] = DEFAULT_ERROR
            context['value'] = old
            return render(req,'View/HTMX/normal_view/normal_view.html',context=context)
                    
        return render(req,'View/HTMX/normal_view/normal_view.html',context=context)
        
    return HttpResponse(status=403)

def edit_image_form(req: HttpRequest, id: str, idx:int) -> HttpResponse:
    if(is_hx_get(req) and is_authenticated(req.user) and is_admin(req.user)):
        column = req.GET.get('column',None)
        
        return render(req,'View/HTMX/edit_form/edit_image_form.html',context={"id":id,"column":column,"idx":idx})
    
    elif (is_hx_post(req) and is_authenticated(req.user) and is_admin(req.user)):
        column = req.POST.get('column',None)
        file = req.FILES.get('file')
        context = {"id":id,"idx":idx,"admin":True,"column":column,}
        
        try:
            buffer = BytesIO()
            with file.open('rb') as f:
                buffer.write(f.read())
            
            img = Image.open(buffer)
            width, height = img.width, img.height
            buffer.seek(0)
            
            with BytesIO() as b:
                img.save(b,format=img.format,quality=95)
                img_data = f"{width}:{height}:{b64encode(buffer.getvalue()).decode()}"
        
        except Exception as e:
            APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,taskID=id,user=req.user,exception=e))
            context['error'] = DEFAULT_ERROR
        
        conn = MongoConnection().connect()
        res = None
        try:
            column_name = f"data.excel.{column}.{idx}"
            feed_idx = f"data.feed.{idx}.index"
            lock_idx = f"data.feed.{idx}.locked"
            
            if("search" in context):
                img_data = conn.find_one({"_id":ObjectId(id)},{column_name:1}).get("data",{}).get("excel",{}).get(column,{}).get(str(idx),"")
            else:
                res = conn.update_one({"_id":ObjectId(id),column_name:{"$exist":True},feed_idx:idx,lock_idx:{"$ne":True},"data.header.image_column":column},{"$set":{column_name:img_data}})
                file_name = conn.find_one({"_id":ObjectId(id)},{"data.header.file_name":1}).get("data",{}).get("header",{}).get("file_name",None)
            
                if(res):
                    APP_LOG.write_info(LogStructure().set_request(req).set_description(type=Task.DATA_EDIT,taskID=id,index=idx,column=column,user=req.user,fileName=file_name))
                else:
                    context['error'] = "Cannot Edit this index is locked"
                    context['lock'] = True
                    return render(req,'View/HTMX/normal_view/normal_image.html',context=context)
                
            context.update({'value':img_data})
            
        except Exception as e:
            APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,taskID=id,index=idx,user=req.user,exception=e))
            context['error'] = DEFAULT_ERROR
            return render(req,'View/HTMX/normal_view/normal_image.html',context=context)
                    
        return render(req,'View/HTMX/normal_view/normal_image.html',context=context)
        
    return HttpResponse(status=403)

def normal_image(req: HttpRequest, id: str, idx:int) -> HttpResponse:
    if(is_hx_get(req) and is_authenticated(req.user) and is_admin(req.user)):
        column = req.GET.get('column',None)
        return render(req,'View/HTMX/normal_view/normal_image.html',context={"id":id,"column":column,"idx":idx})
    return HttpResponse(status=403)

def normal_view(req: HttpRequest, id: str, idx:int) -> HttpResponse:
    if(is_hx_get(req) and is_authenticated(req.user) and is_admin(req.user)):
        column = req.GET.get('column',None)
        value = req.GET.get("value","")
        return render(req,'View/HTMX/normal_view/normal_view.html',context={"id":id,"column":column,"idx":idx,"value":value,"admin":True})
    return HttpResponse(status=403)

@csrf_exempt
def issued_view(req:HttpRequest, id:str, idx: int, token:str) -> JsonResponse:
    if(req.method=="POST"):
        api_key = req.POST.get("api_key",None)
        secure_key = req.POST.get("secure_key",None)
        status = req.POST.get("status",None)
        
        if(api_key==settings.API_KEY and secure_key==settings.SECURE_KEY):
            
            conn = MongoConnection().connect()
            Redis = RedisConnection().connect()
            
            match(status):
                case "true": status = True
                case "false": status = False
                case _: status = None
                
            error:str = None
            res = False
            
            try:
                time_of_issue = f"data.feed.{idx}.time_of_issue"
                issued = f"data.feed.{idx}.issued"            
                feed_idx = f"data.feed.{idx}.index"
                lock_idx = f"data.feed.{idx}.locked"

                file_name = conn.find_one({"_id":ObjectId(id)},{"data.header.file_name":1}).get("data",{}).get("header",{}).get("file_name",None)
                
                if(Redis.get(token)!=LOADING):
                    APP_LOG.write_info(LogStructure().set_request(req).set_description(type=Task.INVALID_TOKEN,taskID=id,index=idx,fileName=file_name))
                    return JsonResponse(data={"error_occurred":"Invalid Token", "update_occurred":False}, status=404)
                
                if(status):
                    res = conn.update_one({"_id":ObjectId(id),feed_idx:idx,lock_idx:True},{"$set":{time_of_issue:timezone.now().isoformat(),issued:status}})
                    Redis.set(token,DONE)
                else:
                    Redis.set(token,FAILED)
                    
                
                if(res and status):
                    APP_LOG.write_info(LogStructure().set_request(req).set_description(type=Task.CARD_READ,taskID=id,index=idx,fileName=file_name))
                
                elif(res and (status is not None)):
                    APP_LOG.write_info(LogStructure().set_request(req).set_description(type=Task.CARD_CANCEL,taskID=id,index=idx,fileName=file_name))
                
                
            except Exception as e:
                APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,taskID=id,index=idx,exception=e))
                error = DEFAULT_ERROR
                
            finally:
                conn.close()
                Redis.close()
                
            return JsonResponse(data={"error_occurred":error, "update_occurred":res},status=200)
    
        else:
            APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.UNAUTH_REQ,taskID=id,index=idx))
    
    return JsonResponse(data=ERROR_JSON, status=403)
    
@csrf_exempt
def fetch_view(req:HttpRequest, id:str, idx: int, token:str) -> JsonResponse:
    if(req.method=="POST"):
        api_key = req.POST.get("api_key",None)
        secure_key = req.POST.get("secure_key",None)

        if(api_key==settings.API_KEY and secure_key==settings.SECURE_KEY):
            conn = MongoConnection().connect()
            Redis = RedisConnection().connect()
            
            result:dict[str,Any] = {"data":"Default Data"}
            
            try:
                res:dict[str,dict[str,dict[str,str]]] = conn.find_one({"_id":ObjectId(id)})   
                file_name = res.get("data",{}).get("header",{}).get("file_name",None)
                verified:bool = res.get("data",{}).get("feed",{})[idx].get("locked", False)
                
                if(Redis.get(token)!=LOADING):
                    APP_LOG.write_info(LogStructure().set_request(req).set_description(type=Task.INVALID_TOKEN,taskID=id,index=idx,fileName=file_name))
                    return JsonResponse(data={"error":"Invalid Token"}, status=403, safe=False)
                if(verified):
                    result.update({"data":{"data":compress_data(res,idx,False,True).getvalue().decode()}, "status":200})
                else:
                    result.update({"data":{"error":f"Mongo ID: {id}, Index: {idx} is not locked"}, "status":403})
                    
                APP_LOG.write_info(LogStructure().set_request(req).set_description(type=Task.CARD_DATA_FETCH,user=req.user,taskID=id,fileName=file_name,index=idx))
            
            except Exception as e:
                APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,taskID=id,index=idx,user=req.user,exception=e))
                result.update({"data":{"error":"Some error occurred!"},"status":500})
            finally:
                conn.close()
                Redis.close()

            return JsonResponse(**result,safe=False)
    
    return JsonResponse(data=ERROR_JSON,status=403)