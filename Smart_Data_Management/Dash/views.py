from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from Main.models import MongoConnection, get_error_info
from django.urls import reverse
from django.conf import settings
from User.models import get_post_id, get_user_by_id, is_authenticated, is_admin, is_manager, is_uploader
from tools.url_auth import *
from tools.encrypt import decrypt_data
import typing
from PIL import Image
import re


VIEW_DATA = {"_id":1,"header.manager":1,"header.uploader":1,"data.header.file_name":1}

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
        
        try:
            conn = MongoConnection(settings.MONGO_URL)
            excel = conn.connect(settings.MONGO_CRED)
            
            result:list[dict[str,dict[str,dict|str|list]]] = excel.find({"header.uploader":req.user.id},VIEW_DATA)
            
            for i in result:
            
                upload.append({'id':i.get('_id'), 'uploader':get_user_by_id(i.get('header',{}).get('uploader')), 'manager':[get_user_by_id(j) for j in i.get('header',{}).get('manager',[])],'file_name':i.get('data',{}).get('header',{}).get('file_name')})
            
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
        
        try:
            conn = MongoConnection(settings.MONGO_URL)
            excel = conn.connect(settings.MONGO_CRED)
            
            result:list[dict[str,dict[str,dict|str|list]]] = excel.find({"header.manager":req.user.id},VIEW_DATA)
            for i in result:            
                manage.append({'id':i.get('_id'), 'uploader':get_user_by_id(i.get('header',{}).get('uploader')), 'manager':[get_user_by_id(j) for j in i.get('header',{}).get('manager',[])],'file_name':i.get('data',{}).get('header',{}).get('file_name')})
            print(manage)
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
        
        try:
            conn = MongoConnection(settings.MONGO_URL)
            excel = conn.connect(settings.MONGO_CRED)
            
            result:list[dict[str,dict[str,dict|str|list]]] = excel.find({"header.post":get_post_id(req.user),'header.manager':[]},VIEW_DATA)
            
            for i in result:
            
                admin.append({'id':i.get('_id'), 'uploader':get_user_by_id(i.get('header',{}).get('uploader')), 'manager':[get_user_by_id(j) for j in i.get('header',{}).get('manager',[])],'file_name':i.get('data',{}).get('header',{}).get('file_name')})
            
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
        
        try:
            conn = MongoConnection(settings.MONGO_URL)
            excel = conn.connect(settings.MONGO_CRED)
            
            result:list[dict[str,dict[str,dict|str|list]]] = excel.find({"header.post":get_post_id(req.user),'header.manager':{"$ne":[]}},VIEW_DATA)
            print(result)
            for i in result:
            
                admin.append({'id':i.get('_id'), 'uploader':get_user_by_id(i.get('header',{}).get('uploader')), 'manager':[get_user_by_id(j) for j in i.get('header',{}).get('manager',[])],'file_name':i.get('data',{}).get('header',{}).get('file_name')})
            
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

def read_screen(req: HttpRequest) -> HttpResponse:
    if(not (is_authenticated(req.user) and (is_manager(req.user)))):
        return redirect(reverse(settings.LOGIN_URL) + '?alert=Unauthenticated Request')

    # simulate read card
    try:
        with open(settings.MEDIA_ROOT + '/compress.txt','r') as f:
            data:dict[str,dict[str,str]] = decrypt_data(settings.KEY,f.read())
    except Exception as e:
        return redirect(reverse('Excel:dash') + f'?alert=Failed to read card ({e})')
        
        
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

    return render(req,'Dash/read.html',context={'data':result,'personal':view.personal_info,'pic':view.profile_img,'sem_dict':view.sem_data,**header})




