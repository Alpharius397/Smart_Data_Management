from base64 import b64decode, b64encode
from io import BytesIO
import json
import re
from PIL import Image
from typing import NamedTuple, Any
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse, FileResponse
from Main.models import *
from django.conf import settings
from tools.get_image import compress_image
from User.models import Admin, Manager, get_post_id, is_admin, is_manager, is_authenticated, get_post, get_user_by_id
import pandas as pd
from bson.objectid import ObjectId
from django.contrib.auth.models import User
from tools.encrypt import encrypt_data, decrypt_data
from Main.templatetags.bad_image import bad_image
from tools.url_auth import is_hx_get, is_auth_get, is_hx_post, auth_needed
from View.forms import VerifyForm
from django.utils import timezone
from Main.loggers import AppLogger, LogStructure

MAX_RECORD:int = 5
log = AppLogger(settings.DATA_FILE)
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
        print(LogStructure().set_request(req).get_log())
        return render(req,'View/table/admin.html',{'id':id})
    
    elif(is_manager(req.user)):
        return render(req,'View/table/manager.html',{'id':id})    
    
    return HttpResponse(status=403)

def search_query(pd_data:pd.DataFrame,column:str,value:str,available_column:list) -> tuple[bool,pd.DataFrame]:
    
    if((column and value) and (column in available_column) and (column in pd_data.columns)):
        pd_data = pd_data[pd_data[column].astype(str).str.contains(value)]

    return (pd_data.empty,pd_data)

def get_context(user:User,id:str,conn:MongoConnection, column:str = None, value:str = None, page:str = '0') -> dict[str,str]:
    
    result:dict[str,dict[str,dict]] = None
    context = {'id':id}
    search = False
    conn.connect()
    
    try:
        if(is_manager(user)):
            result = conn.find_one({"$and":[{"_id":ObjectId(id),"header.manager":user.id}]})
            
        elif(is_admin(user)):
            result = conn.find_one({"$and":[{"_id":ObjectId(id),"header.post":get_post_id(user)}]})
            
    except Exception as e:
        context['search'] = log.write_info()
        return context
    finally:
        conn.close()
    
    
    if(result is None):
        context['search'] = "Mongo ID %s was not found" % id
        return context
    
    try:
        page = int(page)
        pd_data = pd.DataFrame(result.get('data',{}).get('excel',{}))
        image_idx:list = result.get('data',{}).get('header',{}).get('image_column',[])
        verify_idx:list = [i.get('status') for i in list(result.get('data',{}).get('feed',{}).values())[page:page+MAX_RECORD]]
        available_column = sorted(list(set(pd_data.columns.to_list()) - set([ i for i in image_idx])))
        uploader = get_user_by_id(result.get('header',{}).get('uploader',None))
        manager = [get_user_by_id(i) for i in result.get('header',{}).get('manager',[])]
        search, pd_data = search_query(pd_data,column,value,available_column)
        pd_data = pd_data.iloc[page:page+MAX_RECORD]

    except Exception as e:
        context['search'] = AppLogger.get_error_info(e)
        return context
    
    if(search):
        context['search'] = "No matching records found"
    else:
        context.update({'column':pd_data.columns,'upload':uploader,'manage':manager,'result':pd_data.iterrows(),'image':image_idx,'verify':verify_idx,'available':available_column,'max_record':page+MAX_RECORD})

    return context


def data_view(req: HttpRequest,id) -> HttpResponse:

    if(is_auth_get(req)):
    
        connection = MongoConnection(settings.MONGO_URL)
        excel = connection.connect(settings.MONGO_CRED)            
        context = get_context(req.user,id,excel)
        connection.connection.close()
        context.update({"admin":is_admin(req.user)})
        return render(req,'View/HTMX/page.html',context=context)
    
    else:
        return auth_needed(req)


def assign_form(req:HttpRequest, id:str) -> HttpResponse:
    
    if(is_authenticated(req.user) and is_hx_get(req) and is_admin(req.user)):
        
        connection = MongoConnection(settings.MONGO_URL)
        excel = connection.connect(settings.MONGO_CRED) 
        result:dict[str,dict[str,dict]] = None
        context = {'id':id}

        
        try:
            result = excel.find_one({"$and":[{"_id":ObjectId(id),"header.post":get_post_id(req.user)}]},{"header.uploader":1,"header.manager":1})
            
        except Exception as e:            
            context['error'] = AppLogger.get_error_info(e)
            return render(req,'View/HTMX/form.html',context=context)
        finally:
            connection.connection.close()
        try:
            user:Admin = req.user
            uploader = get_user_by_id(result.get('header',{}).get('uploader',None))
            manager = {i:get_user_by_id(i) for i in result.get('header',{}).get('manager',[])}
            all_manager = {i.get('user_id'):get_user_by_id(i.get('user_id')) for i in Manager.objects.filter(belongs__id=user.admin.belongs.id).exclude(user__id__in=list(manager.keys())).values()}
            
            context.update({'upload':uploader,'manage':manager,'option':all_manager})
            
        except Exception as e:
            context['error'] = AppLogger.get_error_info(e)

        return render(req,'View/HTMX/form.html',context=context)
    
    
    elif(is_authenticated(req.user) and is_hx_post(req) and is_admin(req.user)):
        
        connection = MongoConnection(settings.MONGO_URL)
        excel = connection.connect(settings.MONGO_CRED) 
        result:dict[str,dict[str,dict]] = None
        context = {'id':id}

        user:str = req.POST.get('user',None)
        to_do = req.POST.get('to_do',None)

        match to_do:
            case "assign": to_do = True
            case "delete": to_do = False
            case _: to_do = None
        
        if(to_do is None or user is None):
            context['error'] = "User not found"
            return render(req,'View/HTMX/message.assign.html',context=context)
            
            
        try:
            result = excel.find_one({"$and":[{"_id":ObjectId(id),"header.post":get_post_id(req.user)}]},{"header.manager":1})
            
        except Exception as e:
            context['error'] = AppLogger.get_error_info(e)
            return render(req,'View/HTMX/message.assign.html',context=context)
            
        
        try:
            manager = [i for i in result.get('header',{}).get('manager',[])]
            all_manager = [get_user_by_id(i.get('user_id')) for i in Manager.objects.filter(belongs__id=req.user.admin.belongs.id).exclude(user__id__in=manager).values()]
            _manage = Manager.objects.get(user__id=user)
        except Exception as e:
            context['error'] = AppLogger.get_error_info(e)
            return render(req,'View/HTMX/message.assign.html',context=context)
        
        try:
            if(to_do):
                manager.append(_manage.user.id)
                manager = list(set(manager))
                
                excel.update_one({"$and":[{"_id":ObjectId(id),"header.post":get_post_id(req.user)}]},{"$set":{'header.manager':manager}})
                context['msg'] = "Add Manager %(manage)s to task ID %(id)s" % {'manage':_manage.user.username,'id':id}
            else:
                manager.remove(_manage.user.id)
                manager = list(set(manager))
                
                excel.update_one({"$and":[{"_id":ObjectId(id),"header.post":get_post_id(req.user)}]},{"$set":{'header.manager':manager}})
                context['msg'] = "Removed Manager %(manage)s from task ID %(id)s" % {'manage':_manage.user.username,'id':id}

        except Exception as e:
            context['error'] = AppLogger.get_error_info(e)
            return render(req,'View/HTMX/message.assign.html',context=context)
        
        finally:
            connection.connection.close()
            
        return render(req,'View/HTMX/message.assign.html',context=context)
            

    return HttpResponse(status=403)


def table_query(req: HttpRequest, id:str) -> HttpResponse:
    
    if((is_authenticated(req.user)) and is_hx_get(req)):
        
        connection = MongoConnection(settings.MONGO_URL)
        excel = connection.connect(settings.MONGO_CRED)
        column = req.GET.get('column',None)
        value = req.GET.get('search',None)
        page = req.GET.get('page','0')
        
        context = get_context(req.user,id,excel,column,value,page)
        context.update({"admin":is_admin(req.user)})
        connection.connection.close()
        return render(req,'View/HTMX/table.html',context=context)
    
    return HttpResponse(status=403)

def row_view(req: HttpRequest, id:str) -> HttpResponse:
    
    if((is_authenticated(req.user)) and is_hx_get(req)):
        
        connection = MongoConnection(settings.MONGO_URL)
        excel = connection.connect(settings.MONGO_CRED)
        
        column = req.GET.get('column',None)
        value = req.GET.get('search',None)
        page = req.GET.get('page','0')

        context = get_context(req.user,id,excel,column,value,page)
        context.update({"admin":is_admin(req.user)})
        connection.connection.close()
        
        return render(req,'View/HTMX/row.html',context=context)
    
    return HttpResponse(status=403)
    

def quick_query(req: HttpRequest, id:str):
    if((is_authenticated(req.user)) and is_hx_get(req)):
    
        connection = MongoConnection(settings.MONGO_URL)
        excel = connection.connect(settings.MONGO_CRED)
        column = req.GET.get('column',None)
        search = req.GET.get('search','')
        context = {'option':[]}
        
        try:
            result:dict[str,dict[str,dict]] = excel.find_one({"$and":[{"_id":ObjectId(id),"$or":AUTH_VIEW(req.user)}]},{"data.excel":1})
            pd_data = pd.DataFrame(result.get('data',{}).get('excel',{}))
            if(column in pd_data.columns):
                pd_data = pd_data[pd_data[column].str.contains(search)][column].to_numpy()
                context['option'] = [i for i in sorted(set(pd_data))[:5]]    
        except Exception as e:
            print(AppLogger.get_error_info(e))
            
        return render(req,'View/HTMX/suggests.html',context=context)
    
    
def index_view(req: HttpRequest, id:str, idx:int) -> HttpResponse:
    
    if(is_hx_get(req)):
        return report_view(req,id,idx)
    
    elif(is_hx_post(req)):
        return report_view(req,id,idx)
    
    elif(not (is_authenticated(req.user))):
        return auth_needed(req)
    
    else:
        return render(req,'View/single.html',{'id':id,'idx':idx,'manage':is_manager(req.user)})

    
def report_view(req: HttpRequest, id:str, idx:int) ->HttpResponse:

    if(is_authenticated(req.user) and is_hx_get(req)):
        
        connection = MongoConnection(settings.MONGO_URL)
        excel = connection.connect(settings.MONGO_CRED)
        context = {'id':id,'idx':idx}
        
        try:
            result:dict[str,dict[str,dict]] = excel.find_one({"$and":[{"_id":ObjectId(id),"$or":AUTH_VIEW(req.user)}]},{"data.feed":1,"data.excel":1})
            meta_data:dict = result.get('data',{}).get('feed',{}).get(str(idx),{})
            pd_data = pd.DataFrame(result.get('data',{}).get('excel',{})).iloc[idx]
            
        except Exception as e:
            print(e)
            context['search'] = AppLogger.get_error_info(e)
            return render(req,'View/HTMX/report.html',context=context)
        
        finally:
            connection.connection.close()
            
        if(pd_data.empty or (not meta_data)):
            context['search'] = "Mongo ID %s and index %s not found!" % id,idx
            return render(req,'View/HTMX/report.html',context=context)
        
        else:
            pd_data = pd_data.to_dict()
            report = report_structure(pd_data)
            
            context.update({'data':pd_data,'personal':report.personal_info,'pic':report.profile_img,'sem_dict':report.sem_data,**get_post(req.user),**meta_data})
            
        return render(req,'View/HTMX/report.html',context=context)
    
    return HttpResponse(status=403)
    
def feed_view(req: HttpRequest, id:str, idx:int) ->HttpResponse:

    if(is_authenticated(req.user) and is_hx_post(req) and is_manager(req.user)):
        
        connection = MongoConnection(settings.MONGO_URL)
        excel = connection.connect(settings.MONGO_CRED)
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
                column = f"data.feed.{idx}"
                status_col = f"{column}.status"
                feed_col = f"{column}.feed"
                success = excel.update_one({"$and":[{"_id":ObjectId(id),"$or":AUTH_VIEW(req.user),column:{"$exists":True}}]},{"$set":{status_col:status,feed_col:feed}}).matched_count
                
                if(success==1):
                    context['msg'] = "Status Updated!"
                else:
                    context['search'] = "Mongo ID %s not found" % id
                    
            except Exception as e:
                context['search'] = AppLogger.get_error_info(e)
                
            finally:
                connection.connection.close()    
        else:
            context['search'] = f.errors.as_text()
            
        return render(req,'View/HTMX/message.issue.html',context=context)
    
    elif(is_authenticated(req.user) and is_hx_get(req) and is_manager(req.user)):
        connection = MongoConnection(settings.MONGO_URL)
        excel = connection.connect(settings.MONGO_CRED)
        context = {'id':id,'idx':idx}
        
        try:
            result:dict[str,dict[str,dict]] = excel.find_one({"$and":[{"_id":ObjectId(id),"header.manager":req.user.id}]},{"data.feed":1,"header.manager":1})
            meta_data:list[dict] = result.get('data',{}).get('feed',{}).get(str(idx),{})
            manager:list[str] = [get_user_by_id(i) for i in result.get('header',{}).get('manager',[])]
            context.update({**meta_data,'manager':manager})
            print(result)
        except Exception as e:
            context['search'] = AppLogger.get_error_info(e)
        finally:
            connection.connection.close()
        
        context.update({'form':VerifyForm(data={'status':(lambda x: 'True' if x else ('False') if x is not None else ('None'))(context.get('status','None')),'feed':context.get('feed','')})})
        return render(req,'View/single/manager.html',context=context)
    
    elif(is_authenticated(req.user) and is_hx_get(req)):
        connection = MongoConnection(settings.MONGO_URL)
        excel = connection.connect(settings.MONGO_CRED)
        context = {'id':id,'idx':idx}
        
        try:
            result:dict[str,dict[str,dict]] = excel.find_one({"$and":[{"_id":ObjectId(id),"$or":AUTH_VIEW(req.user)}]},{"data.feed":1,"header.manager":1})
            meta_data:dict = result.get('data',{}).get('feed',{}).get(str(idx),{})
            manager:list[str] = [get_user_by_id(i) for i in result.get('header',{}).get('manager',[])]
            print(manager)
            context.update({**meta_data,'manager':manager})
            
        except Exception as e:
            context['search'] = AppLogger.get_error_info(e)
            
        finally:
            connection.connection.close()
            
            return render(req,'View/single/admin.html',context=context)
        
    return HttpResponse(status=403)
            
def compress_view(req: HttpRequest, id:str, idx:int) -> HttpResponse:
    
    if(is_authenticated(req.user) and is_manager(req.user)):
        
        if(is_hx_get(req)):
            
            connection = MongoConnection(settings.MONGO_URL)
            excel = connection.connect(settings.MONGO_CRED)
            context = {'id':id,'idx':idx}
            try:
                feed_col = f"data.feed.{idx}"
                result:dict[str,dict[str,dict]] = excel.find_one({"$and":[{"_id":ObjectId(id),"$or":AUTH_VIEW(req.user)}]},{feed_col:1})
                meta_data:dict = result.get('data',{}).get('feed',{}).get(str(idx),{})
                context.update({**meta_data})
                print(context,result)
            except Exception as e:
                print(AppLogger.get_error_info(e))
                return render(req,'View/single/manager_form.html',context=context)

            return render(req,'View/single/manager_form.html',context=context)
        
        elif(is_hx_post(req)):
            to_do = req.POST.get("to_do")
            
            connection = MongoConnection(settings.MONGO_URL)
            excel = connection.connect(settings.MONGO_CRED)
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
                time_issue = f"data.feed.{idx}.time_of_issue"
                locked_col = f"data.feed.{idx}.locked"
                res = excel.update_one({"_id":ObjectId(id)},{"$set":{time_issue:timestamp,locked_col:locked}}).modified_count

                if(res==1 and locked): 
                    context['msg'] = "Card Issued"
                elif(res==1): 
                    context['msg'] = "Card Cancelled"
                    
                else: context['search'] = "Data update failed"
            
            except Exception as e:
                context['search'] = AppLogger.get_error_info(e)
                return render(req,'View/HTMX/message.issue.html',context=context)
            
            finally:
                connection.connection.close()
            
            return render(req,'View/HTMX/message.issue.html',context=context)
        
    return HttpResponse(status=403)
            
def compress_data(result:dict[str,dict[str,dict]], manager:User, idx:int, local_write:bool = True) -> BytesIO:
    
    pd_data = pd.DataFrame(result.get('data',{}).get('excel',{}))
    image_idx:list = result.get('data',{}).get('header',{}).get('image_column',[])
    belongs = get_user_by_id(result.get('header',{}).get('uploader',None))
    data = pd_data.iloc[idx].to_dict()
    timestamp = timezone.now().isoformat()

    for i in image_idx:
        img_data = data[i]
        
        raw_img = img_data.split(':')
    
        try:
            _, _, img = raw_img
        except:
            img = bad_image
            
        img = compress_image(BytesIO(b64decode(img)))
        
        data[i] = img
        
    send_data = {'header':{'manager':manager.username,**get_post(manager),'uploader':belongs ,'time':timestamp},'data':data}


    if(local_write):
        with open(settings.MEDIA_ROOT + '/compress.txt','w') as f:
            f.write(encrypt_data(settings.KEY,send_data))
            
        with open(settings.MEDIA_ROOT + '/decompress.txt','w') as f:
            f.write(json.dumps(decrypt_data(settings.KEY,encrypt_data(settings.KEY,send_data))))
    
    buffer = BytesIO()
    buffer.write(encrypt_data(settings.KEY,send_data).encode())
    buffer.seek(0)
    
    return buffer        

def card_view(req: HttpRequest, id:str, idx:int) -> FileResponse:

    if(is_auth_get(req)):
        connection = MongoConnection(settings.MONGO_URL)
        excel = connection.connect(settings.MONGO_CRED)
        result = None
        try:
            result:dict[str,dict[str,dict]] = excel.find_one({"$and":[{"_id":ObjectId(id),"$or":AUTH_VIEW(req.user)}]})
            
        except Exception as e:
            pass
        

        return FileResponse(compress_data(result,req.user,idx,False),as_attachment=True,filename=f"{id}_{idx}.txt")
    
    
    
def edit_form(req: HttpRequest, id: str, idx:int) -> HttpResponse:
    if(is_hx_get(req) and is_authenticated(req.user) and is_admin(req.user)):
        column = req.GET.get('column',None)
        value = req.GET.get("value","")
        
        return render(req,'View/HTMX/edit_form.html',context={"id":id,"column":column,"idx":idx,"value":value,})
    
    elif (is_hx_post(req) and is_authenticated(req.user) and is_admin(req.user)):
        column = req.POST.get('column',None)
        value = req.POST.get("value",)
        j = req.POST.get("j","")
        old = req.POST.get("old","")
        
        connection = MongoConnection(settings.MONGO_URL)
        excel = connection.connect(settings.MONGO_CRED)
        context = {"id":id,"idx":idx,"value":value,"admin":True,"column":column}
        try:
            column_name = f"data.excel.{column}.{idx}"
            excel.update_one({"_id":ObjectId(id),column_name:{"$exists":True}},{"$set":{column_name:value}})
        except Exception as e:
            context['error'] = AppLogger.get_error_info(e)
            context['value'] = old
            return render(req,'View/HTMX/normal_view.html',context=context)
                    
        return render(req,'View/HTMX/normal_view.html',context=context)
        
    return HttpResponse(status=403)

def edit_image_form(req: HttpRequest, id: str, idx:int) -> HttpResponse:
    if(is_hx_get(req) and is_authenticated(req.user) and is_admin(req.user)):
        column = req.GET.get('column',None)
        
        return render(req,'View/HTMX/edit_image_form.html',context={"id":id,"column":column,"idx":idx})
    
    elif (is_hx_post(req) and is_authenticated(req.user) and is_admin(req.user)):
        column = req.POST.get('column',None)
        value = req.POST.get('value',None)
        file = req.FILES.get('file')
        context = {"id":id,"idx":idx,"admin":True,"column":column,"value":value}
        
        try:
            buffer = BytesIO()
            with file.open('rb') as f:
                buffer.write(f.read())
            
            img = Image.open(buffer)
            width, height = img.width, img.height
            buffer.seek(0)
            with BytesIO() as b:
                img.save(b,format='jpeg',quality=95)
                img_data = f"{width}:{height}:{b64encode(buffer.getvalue()).decode()}"
        
        except Exception as e:
            context['error'] = AppLogger.get_error_info(e)
            return render(req,'View/HTMX/normal_image.html',context=context)
        
        connection = MongoConnection(settings.MONGO_URL)
        excel = connection.connect(settings.MONGO_CRED)
        context = {"id":id,"idx":idx,"admin":True,"column":column}
        try:
            column_name = f"data.excel.{column}.{idx}"
            excel.update_one({"_id":ObjectId(id),column_name:{"$exists":True},"data.header.image_column":column},{"$set":{column_name:img_data}})
            context.update({'value':img_data})
        except Exception as e:
            context['error'] = AppLogger.get_error_info(e)
            return render(req,'View/HTMX/normal_image.html',context=context)
                    
        return render(req,'View/HTMX/normal_image.html',context=context)
        
    return HttpResponse(status=403)

def normal_image(req: HttpRequest, id: str, idx:int) -> HttpResponse:
    if(is_hx_get(req) and is_authenticated(req.user) and is_admin(req.user)):
        column = req.GET.get('column',None)
        return render(req,'View/HTMX/image.html',context={"id":id,"column":column,"idx":idx})
    return HttpResponse(status=403)

def normal_view(req: HttpRequest, id: str, idx:int) -> HttpResponse:
    if(is_hx_get(req) and is_authenticated(req.user) and is_admin(req.user)):
        column = req.GET.get('column',None)
        value = req.GET.get("value","")
        return render(req,'View/HTMX/normal_view.html',context={"id":id,"column":column,"idx":idx,"value":value,"admin":True})
    return HttpResponse(status=403)