from base64 import b64decode
from io import BytesIO
import json
import re
from typing import NamedTuple, Any
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from Main.models import *
from django.urls import reverse
from django.conf import settings
from tools.get_image import compress_image
from User.models import get_post_id, is_manager, is_uploader, is_authenticated, get_post, get_user_by_id
import pandas as pd
from bson.objectid import ObjectId
from django.contrib.auth.models import User
from tools.encrypt import encrypt_data, decrypt_data
from Main.templatetags.bad_image import bad_image
from tools.url_auth import is_hx_get, is_auth_get, is_hx_post
from View.forms import VerifyForm
from django.utils import timezone

MAX_RECORD:int = 5

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
        return redirect(reverse(settings.LOGIN_URL) + '?alert=Unauthenticated Request')
    
    elif(is_uploader(req.user)):
        return render(req,'View/table/uploader.html',{'id':id})
    
    elif(is_manager(req.user)):
        return render(req,'View/table/manager.html',{'id':id})    
    
    else:
        return render(req,'View/table/admin.html',{'id':id})

def search_query(pd_data:pd.DataFrame,column:str,value:str,available_column:list) -> tuple[bool,pd.DataFrame]:
    
    if((column and value) and (column in available_column) and (column in pd_data.columns)):
        pd_data = pd_data[pd_data[column].astype(str).str.contains(value)]

    return (pd_data.empty,pd_data)

def get_context(user:User,id:str,excel:pymongo.collection.Collection, column:str = None, value:str = None, page:str = '0') -> dict[str,str]:
    
    result:dict[str,dict[str,dict]] = None
    context = {'id':id}
    search = False
    
    try:
        if(is_manager(user)):
            result = excel.find_one({"$and":[{"_id":ObjectId(id),"header.manager":user.id}]})
            
        elif(is_uploader(user)):
            result = excel.find_one({"$and":[{"_id":ObjectId(id),"header.uploader":user.id}]})
            
        else:
            result = excel.find_one({"$and":[{"_id":ObjectId(id),"header.post":get_post_id(user)}]})
            
    except Exception as e:
        context['search'] = get_error_info(e)
        return context
    
    if(result is None):
        context['search'] = "Mongo ID %s was not found" % id
        return context
    
    try:
        page = int(page)
        pd_data = pd.DataFrame(result.get('data',{}).get('excel',{}))
        image_idx:list = result.get('data',{}).get('header',{}).get('image_column',[])
        verify_idx:list = [i.get('status') for i in result.get('data',{}).get('feed',[])[page:page+MAX_RECORD]]
        available_column = sorted(list(set(pd_data.columns.to_list()) - set([ i for i in image_idx])))
        uploader = get_user_by_id(result.get('header',{}).get('uploader',None))
        manager = [get_user_by_id(i) for i in result.get('header',{}).get('manager',[])]
        search, pd_data = search_query(pd_data,column,value,available_column)
        pd_data = pd_data.iloc[page:page+MAX_RECORD]

    except Exception as e:
        context['search'] = get_error_info(e)
        return context
    
    if(search):
        context['search'] = "No matching records found"
    else:
        context.update({'column':pd_data.columns,'result':pd_data.iterrows(),'image':image_idx,'verify':verify_idx,'available':available_column,'max_record':page+MAX_RECORD})

    return context


def data_view(req: HttpRequest,id) -> HttpResponse:

    if(is_auth_get(req)):
    
        connection = MongoConnection(settings.MONGO_URL)
        excel = connection.connect(settings.MONGO_CRED)            
        context = get_context(req.user,id,excel)
        
        return render(req,'View/HTMX/page.html',context=context)
    
    else:
        return redirect(reverse(settings.LOGIN_URL) + '?alert=Unauthenticated Request')

def table_query(req: HttpRequest, id:str) -> HttpResponse:
    
    if((is_authenticated(req.user)) and is_hx_get(req)):
        
        connection = MongoConnection(settings.MONGO_URL)
        excel = connection.connect(settings.MONGO_CRED)
        column = req.GET.get('column',None)
        value = req.GET.get('search',None)
        page = req.GET.get('page','0')
        
        context = get_context(req.user,id,excel,column,value,page)
        
        return render(req,'View/HTMX/table.html',context=context)

def row_view(req: HttpRequest, id:str) -> HttpResponse:
    
    if((is_authenticated(req.user)) and is_hx_get(req)):
        
        connection = MongoConnection(settings.MONGO_URL)
        excel = connection.connect(settings.MONGO_CRED)
        
        column = req.GET.get('column',None)
        value = req.GET.get('search',None)
        page = req.GET.get('page','0')

        context = get_context(req.user,id,excel,column,value,page)
        
        return render(req,'View/HTMX/row.html',context=context)

def quick_query(req: HttpRequest, id:str):
    if((is_authenticated(req.user)) and is_hx_get(req)):
    
        connection = MongoConnection(settings.MONGO_URL)
        excel = connection.connect(settings.MONGO_CRED)
        column = req.GET.get('column',None)
        search = req.GET.get('search','')
        context = {'option':[]}
        
        try:
            result:dict[str,dict[str,dict]] = excel.find_one({"$and":[{"_id":ObjectId(id),"$or":[{"header.uploader":req.user.id},{"header.manager":req.user.id}]}]})

            pd_data = pd.DataFrame(result.get('data',{}).get('excel',{}))
            if(column in pd_data.columns):
                pd_data = pd_data[pd_data[column].str.contains(search)][column].to_numpy()
                context['option'] = [i for i in sorted(set(pd_data))[:5]]    

        except Exception as e:
            print(get_error_info(e))
            
        return render(req,'View/HTMX/suggests.html',context=context)
    
    
def index_view(req: HttpRequest, id:str, idx:int) -> HttpResponse:
    
    if(is_hx_get(req)):
        return report_view(req,id,idx)
    
    elif(is_hx_post(req)):
        return report_view(req,id,idx)
    
    elif(not (is_authenticated(req.user))):
        return redirect(reverse(settings.LOGIN_URL) + '?alert=Unauthenticated Request')
    
    else:
        return render(req,'View/single.html',{'id':id,'idx':idx})

    
def report_view(req: HttpRequest, id:str, idx:int) ->HttpResponse:

    if(is_authenticated(req.user) and is_hx_get(req)):
        
        connection = MongoConnection(settings.MONGO_URL)
        excel = connection.connect(settings.MONGO_CRED)
        context = {'id':id,'idx':idx}
        
        try:
            result:dict[str,dict[str,dict]] = excel.find_one({"$and":[{"_id":ObjectId(id),"$or":[{"header.uploader":req.user.id},{"header.manager":req.user.id}]}]})
            meta_data:dict = result.get('data',{}).get('feed',[])[idx:idx+1][0]
            pd_data = pd.DataFrame(result.get('data',{}).get('excel',{})).iloc[idx]
            
        except Exception as e:
            context['search'] = get_error_info(e)
            return render(req,'View/HTMX/report.html',context=context)
            
        if(pd_data.empty or (not meta_data)):
            context['search'] = "Mongo ID %s and index %s not found!" % id,idx
            return render(req,'View/HTMX/report.html',context=context)
        
        else:
            pd_data = pd_data.to_dict()
            report = report_structure(pd_data)
            
            context.update({'data':pd_data,'personal':report.personal_info,'pic':report.profile_img,'sem_dict':report.sem_data,**get_post(req.user),**meta_data})
            
        return render(req,'View/HTMX/report.html',context=context)
    
    
def feed_view(req: HttpRequest, id:str, idx:int) ->HttpResponse:

    if(is_authenticated(req.user) and is_hx_post(req) and is_manager(req.user)):
        
        connection = MongoConnection(settings.MONGO_URL)
        excel = connection.connect(settings.MONGO_CRED)
        context = {'id':id,'idx':idx}
        
        try:
            result:dict[str,dict[str,dict]] = excel.find_one({"$and":[{"_id":ObjectId(id),"$or":[{"header.uploader":req.user.id},{"header.manager":req.user.id}]}]})
            meta_data:list[dict] = result.get('data',{}).get('feed',[])
            _ = meta_data[idx]
            
        except Exception as e:
            context['search'] = get_error_info(e)
            return render(req,'View/HTMX/message.html',context=context)
            
        f = VerifyForm(req.POST)
        
        if(f.is_valid()):
            status, feed = f.cleaned_data.get("status"), f.cleaned_data.get("feedback") 
            
            if(status=='True'):
                status = True
            elif(status=='False'):
                status = False
            else:
                status = None
                MongoTemplate()
                
            meta_data[idx].update({'status':status,'feed':feed})
            
            try:
                success = excel.update_one({"_id":ObjectId(id)},{"$set":{'data.feed':meta_data}}).matched_count
                
                if(success==1):
                    context['msg'] = "Status Updated!"
                else:
                    context['search'] = "Mongo ID %s not found" % id
                    
            except Exception as e:
                context['search'] = get_error_info(e)
                
        else:
            context['search'] = f.errors.as_text()
    
        return render(req,'View/HTMX/message.html',context=context)
    
    elif(is_authenticated(req.user) and is_hx_get(req) and is_manager(req.user)):
        connection = MongoConnection(settings.MONGO_URL)
        excel = connection.connect(settings.MONGO_CRED)
        context = {'id':id,'idx':idx}
        
        try:
            result:dict[str,dict[str,dict]] = excel.find_one({"$and":[{"_id":ObjectId(id),"header.manager":req.user.id}]})
            meta_data:list[dict] = result.get('data',{}).get('feed',[])
            manager:list[str] = [get_user_by_id(i) for i in result.get('header',{}).get('manager',[])]
            feed = meta_data[idx]
            context.update({**feed,'manager':manager})
            
        except Exception as e:
            context['search'] = get_error_info(e)
        
        context.update({'form':VerifyForm(data={'status':(lambda x: 'True' if x else ('False') if x is not None else ('None'))(context.get('status','None')),'feed':context.get('feed','')})})
        return render(req,'View/single/manager.html',context=context)
    
    elif(is_authenticated(req.user) and is_hx_get(req)):
        connection = MongoConnection(settings.MONGO_URL)
        excel = connection.connect(settings.MONGO_CRED)
        context = {'id':id,'idx':idx}
        
        try:
            result:dict[str,dict[str,dict]] = excel.find_one({"$and":[{"_id":ObjectId(id),"$or":[{"header.uploader":req.user.id},{"header.manager":req.user.id}]}]})
            meta_data:list[dict] = result.get('data',{}).get('feed',[])
            manager:list[str] = [get_user_by_id(i) for i in result.get('header',{}).get('manager',[])]
            feed = meta_data[idx]
            context.update({**feed,'manager':manager})
            
        except Exception as e:
            context['search'] = get_error_info(e)
            
            return render(req,'View/single/uploader.html',context=context)
        return render(req,'View/single/uploader.html',context=context)
            
def compress_view(req: HttpRequest, id:str, idx:int) -> HttpResponse:
    
    if(is_authenticated(req.user) and is_manager(req.user)):
        
        if(is_hx_get(req)):
            
            connection = MongoConnection(settings.MONGO_URL)
            excel = connection.connect(settings.MONGO_CRED)
            context = {'id':id,'idx':idx}
            
            try:
                result:dict[str,dict[str,dict]] = excel.find_one({"$and":[{"_id":ObjectId(id),"$or":[{"header.uploader":req.user.id},{"header.manager":req.user.id}]}]})
                meta_data:list[dict] = result.get('data',{}).get('feed',[])
                feed = meta_data[idx]
                context.update({**feed})
                
            except Exception as e:
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
                case _: locked = None
                
            if(locked):
                timestamp = timezone.now().isoformat()
            
            try:
                result:dict[str,dict[str,dict]] = excel.find_one({"$and":[{"_id":ObjectId(id),"$or":[{"header.uploader":req.user.id},{"header.manager":req.user.id}]}]})
                meta_data:list[dict] = result.get('data',{}).get('feed',[])
                feed = meta_data[idx]
                
            except Exception as e:
                context['search'] = get_error_info(e)
                return render(req,'View/HTMX/message.html',context=context)
            
            meta_data[idx].update({'time_of_issue':timestamp,'locked':locked})
            
            try:
                res = excel.update_one({"_id":ObjectId(id)},{"$set":{'data.feed':meta_data}}).matched_count

                if(res==1 and locked): 
                    compress_data(result,req.user,idx)
                    context['msg'] = "Card Issued"
                elif(res==1): 
                    context['msg'] = "Card Cancelled"
                    
                else: context['search'] = "Data update failed"
            
            except Exception as e:
                context['search'] = get_error_info(e)
                return render(req,'View/HTMX/message.html',context=context)
            
            return render(req,'View/HTMX/message.html',context=context)
            
def compress_data(result:dict[str,dict[str,dict]], manager:User, idx:int) -> dict[str,dict[str]]:
    
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

    with open(settings.MEDIA_ROOT + '/compress.txt','w') as f:
        f.write(encrypt_data(settings.KEY,send_data))
        
    with open(settings.MEDIA_ROOT + '/decompress.txt','w') as f:
        f.write(json.dumps(decrypt_data(settings.KEY,encrypt_data(settings.KEY,send_data))))
        
    