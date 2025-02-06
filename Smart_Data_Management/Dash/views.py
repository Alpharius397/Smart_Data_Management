from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from Main.models import MongoConnection, get_error_info
from django.urls import reverse
from django.conf import settings
from User.models import get_post_id, get_user_by_id, is_authenticated, is_admin, is_manager, is_uploader, get_user_id
from tools.url_auth import *
from tools.encrypt import decrypt_data
import typing
from PIL import Image
import re
import pymongo
from bson import ObjectId
from Main.models import *
from django.contrib.auth.models import User

VIEW_DATA = {"_id":1,"header.manager":1,"header.uploader":1,"data.header.file_name":1}

def get_data(result:list[dict[str,dict[str,dict|str|list]]]) -> tuple[bool,dict[str,str|list]]:
    data = []
    empty = True
    for i in result:
        if(empty): empty=False
        data.append({'id':i.get('_id'), 'uploader':get_user_by_id(i.get('header',{}).get('uploader')), 'manager':[get_user_by_id(j) for j in i.get('header',{}).get('manager',[])],'file_name':i.get('data',{}).get('header',{}).get('file_name')})

    return empty,data


def dash_board(req: HttpRequest) -> HttpResponse:
    if(not (is_authenticated(req.user))):
        return redirect(reverse(settings.LOGIN_URL) + '?alert=Unauthenticated Request')
    
    if(is_uploader(req.user)):
        return render(req,'Dash/dash/uploader.html')

    elif(is_manager(req.user)):
        return render(req,'Dash/dash/manager.html')

    else:
        return render(req,'Dash/dash/admin.html')
    
def uploader_fetch(req: HttpRequest) -> HttpResponse:
    
    if(is_authenticated(req.user) and is_uploader(req.user) and is_hx_get(req)):
        
        upload:list[dict[str,str|list]] = []
        error:str = None
        queryset=get_query(req)
        
        try:
            conn = MongoConnection(settings.MONGO_URL)
            excel = conn.connect(settings.MONGO_CRED)
            
            result:list[dict[str,dict[str,dict|str|list]]] = excel.find({**queryset,"header.uploader":req.user.id},VIEW_DATA)
            
            flag,upload = get_data(result)
            if(flag and queryset): error='No matching records found!'
            
        except Exception as e:
            error = get_error_info(e)
            
        finally:
            conn.connection.close()
            
        return render(req,'Dash/HTMX/uploader.html',context={'upload':upload,'error':error})
    
    return HttpResponse(status=403)

def manager_fetch(req: HttpRequest) -> HttpResponse:
    
    if(is_authenticated(req.user) and is_manager(req.user) and is_hx_get(req)):
        
        manage:list[dict[str,str|list]] = []
        error:str = None
        queryset=get_query(req)
        try:
            conn = MongoConnection(settings.MONGO_URL)
            excel = conn.connect(settings.MONGO_CRED)
            
            result:list[dict[str,dict[str,dict|str|list]]] = excel.find({**queryset,"header.manager":req.user.id},VIEW_DATA)
            flag,manage = get_data(result)
            if(flag and queryset): error='No matching records found!'
        except Exception as e:
            error = get_error_info(e)
            
        finally:
            conn.connection.close()
            
        return render(req,'Dash/HTMX/manager.html',context={'manage':manage,'error':error})
    
    return HttpResponse(status=403)
    
    
def admin_upload_fetch(req: HttpRequest) -> HttpResponse:
    
    if(is_authenticated(req.user) and is_admin(req.user) and is_hx_get(req)):
        
        admin:list[dict[str,str|list]] = []
        error:str = None
        queryset=get_query(req)
        
        try:
            conn = MongoConnection(settings.MONGO_URL)
            excel = conn.connect(settings.MONGO_CRED)
            
            result:list[dict[str,dict[str,dict|str|list]]] = excel.find({**queryset,"header.post":get_post_id(req.user),'header.manager':[]},VIEW_DATA)
            flag,admin = get_data(result)
            if(flag and queryset): error='No matching records found!'
            
        except Exception as e:
            error = get_error_info(e)
            
        finally:
            conn.connection.close()
            
        return render(req,'Dash/HTMX/admin.uploader.html',context={'upload':admin,'error':error})
    
    return HttpResponse(status=403)
    

def admin_manage_fetch(req: HttpRequest) -> HttpResponse:
    
    if(is_authenticated(req.user) and is_admin(req.user) and is_hx_get(req)):
        
        admin:list[dict[str,str|list]] = []
        error:str = None
        queryset=get_query(req)
        
        try:
            conn = MongoConnection(settings.MONGO_URL)
            excel = conn.connect(settings.MONGO_CRED)
            
            result:list[dict[str,dict[str,dict|str|list]]] = excel.find({**queryset,"header.post":get_post_id(req.user),'header.manager':{"$ne":[]}},VIEW_DATA)
            flag,admin = get_data(result)
            if(flag and queryset): error='No matching records found!'

        except Exception as e:
            error = get_error_info(e)
            
        finally:
            conn.connection.close()
            
        return render(req,'Dash/HTMX/admin.manager.html',context={'manage':admin,'error':error})

    return HttpResponse(status=403)

class ReportStructure(typing.NamedTuple):
    profile_img:Image
    personal_info:dict[str,str]
    sem_data:dict[dict[str,str]]
    
def read_view(req: HttpRequest)-> HttpResponse:
    
    if(is_authenticated(req.user) and is_hx_get(req) and is_manager(req.user)):
        context = {}
            
        try:
            with open(settings.MEDIA_ROOT + '/compress.txt','r') as f:
                data:dict[str,dict[str,str]] = decrypt_data(settings.KEY,f.read())
        except Exception as e:
            context['error'] = get_error_info(e)
            
            return render(req,'HTMX/read.card.html',context=context)
        
        profile_img = r'^Profile_Image$'
        sem_data = r'.+Sem_(\d+)$'
        
        result, header = data.get('data',{}), data.get('header',{})
        
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

        view = ReportStructure(profile_img=profile_col,personal_info=personal_col,sem_data=sem_dict)
        context.update({'data':result,'personal':view.personal_info,'pic':view.profile_img,'sem_dict':view.sem_data,**header})

        return render(req,'Dash/HTMX/read.card.html',context=context)

    return HttpResponse(status=403)

def read_screen(req: HttpRequest) -> HttpResponse:
    if(not (is_authenticated(req.user) and (is_manager(req.user)))):
        return redirect(reverse(settings.LOGIN_URL) + '?alert=Unauthenticated Request')

    return render(req,'Dash/read.html')

def get_query(req: HttpRequest) -> dict[str,str]:
    
    query = req.GET.get('query',None)
    value = req.GET.get('value',None)
    query_dict = {}
    print(query,value)
    if(query and value):
        
        if(query=='uploader'):
            query_dict.update({"header.uploader":get_user_id(value)})
        elif(query=='manager'):
            query_dict.update({"header.manager":get_user_id(value)})
        elif(query=='file_name'):
            query_dict.update({"data.header.file_name":value})
        
    return query_dict

        