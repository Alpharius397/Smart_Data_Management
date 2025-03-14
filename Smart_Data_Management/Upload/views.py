from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from Upload.forms import ExcelForm
from Main.models import MongoConnection, MongoTemplate
from Logs.loggers import APP_LOG, LogStructure, DEFAULT_ERROR, Task
from User.models import is_admin, is_authenticated
import json
from bson.objectid import ObjectId
from tools.get_image import image_load
from tools.url_auth import is_auth_get, is_hx_post, auth_needed
from User.models import get_post_id
from django.contrib import messages

# Create your views here.
def upload_screen(req:HttpRequest):
    
    if(not (is_authenticated(req.user) and is_admin(req.user))):
        return auth_needed(req)
    
    if(is_auth_get(req)):        
        f = ExcelForm(initial={'username':req.user.username})
    
        return render(req,'Upload/upload.html',{'form':f})

def edit_screen(req: HttpRequest, id:str) -> HttpResponse:
    if(not (is_authenticated(req.user) and is_admin(req.user))):
        return auth_needed(req)
    
    if(is_auth_get(req)):        
        f = ExcelForm(initial={'username':req.user.username})
    
        return render(req,'Upload/edit.html',{'form':f,'id':id})

def delete(req: HttpRequest, id:str) -> HttpResponse:
    
    if(not (is_authenticated(req.user) and is_admin(req.user))):
        return auth_needed(req)
    
    if(is_auth_get(req)):
    
        return render(req,'Upload/delete.html',{'id':id})

    elif(is_authenticated(req.user) and is_hx_post(req)):
        conn = MongoConnection().connect()
        result = None
        locked = False
        
        try:
            result = conn.find_one({"_id":ObjectId(id),"header.uploader":req.user.id})
            locked = any([i.get('locked') for i in result.get('data',{}).get('feed',[])])
            
        except Exception as e:
            msg = LogStructure().set_request(req).set_description(type=Task.EXCEPTION,user=req.user,exception=e)
            APP_LOG.write_error(msg)
            conn.close()
            messages.error(req,"MongoDB connection failed")
            return render(req,'Upload/HTMX/message.html')
        
        if(result is None):
            messages.error(req,"MongoDB ID %s not found!" % id)
            
        elif(locked):
            messages.error(req,"Data is Locked. Deletion not possible!")
            
        else:
            
            try:
                if(conn.delete_one({"_id":ObjectId(id),"header.uploader":req.user.id})):
                    messages.success(req,"MongoDB ID %s was deleted successfully!" % id)
                else:
                    messages.error(req,"MongoDB ID %s was not deleted!" % id)
                    
            except Exception as e:
                APP_LOG.write_error( LogStructure().set_request(req).set_description(type=Task.EXCEPTION,user=req.user,exception=e))       
                messages.error(req,DEFAULT_ERROR)
                conn.close()
                
                
        return render(req,'Upload/HTMX/message.html')
        
    return HttpResponse(status=403)

    
def upload(req: HttpRequest) -> HttpResponse:

    if((is_authenticated(req.user) and is_admin(req.user)) and is_hx_post(req)):

        f = ExcelForm(req.POST,req.FILES)
    
        conn = MongoConnection().connect()
        pd_data = None
        
        if(not conn.is_connected()):
            messages.error(req,"MongoDB connection failed")
            return render(req,'Upload/HTMX/message.html')
    
        if(f.is_valid()):
            excel_file = req.FILES["file"]
            file_name = f.cleaned_data.get("file_name")
            
            try:
                res = conn.find_one({"data.header.file_name":file_name},{"data.header.file_name":1})
                
                if(res):
                    messages.error(req, "File Name already exists. Please choose a different one!")
                    return render(req,'Upload/HTMX/message.html')
                    
                
            except Exception as e:
                APP_LOG.write_error( LogStructure().set_request(req).set_description(type=Task.EXCEPTION,user=req.user,exception=e))    
                messages.error(req,DEFAULT_ERROR)
                conn.close()
                
                return render(req,'Upload/HTMX/message.html')
                
            try:
                with excel_file.open() as file:
                    image_idx, pd_data = image_load(file.read())
                    
                    if(pd_data is None):
                        messages.error(req,"Data Extraction failed")
                        return render(req,'Upload/HTMX/message.html')
                    
                    rows, _ = pd_data.shape
                    pd_data = pd_data.to_json()
                    
            except Exception as e:
                APP_LOG.write_error( LogStructure().set_request(req).set_description(type=Task.EXCEPTION,user=req.user,exception=e))    
                conn.close()
                messages.error(req,DEFAULT_ERROR)
                return render(req,'Upload/HTMX/message.html')
            
            template = MongoTemplate().add_post(**get_post_id(req.user)).add_image(image_idx).add_excel(json.loads(pd_data)).add_file(file_name).add_uploader(req.user.id).add_feed(rows)
            
            try:
                res = conn.insert_one(template)
                messages.success(req,"Data Insertion successful. Data inserted with Mongo ID:%s" % res)
            except Exception as e:
                APP_LOG.write_error( LogStructure().set_request(req).set_description(type=Task.EXCEPTION,user=req.user,exception=e))    
                messages.error(req,DEFAULT_ERROR)
            finally:
                conn.close()
        else:
            messages.error(req, "Invalid form. %s" % f.errors.as_text())
        
        return render(req,'Upload/HTMX/message.html')
    
    return HttpResponse(status=403)
    

def edit(req: HttpRequest, id:str) -> HttpResponse:

    if((is_authenticated(req.user) and is_admin(req.user)) and is_hx_post(req)):

        f = ExcelForm(req.POST,req.FILES)
    
        conn = MongoConnection().connect()
        pd_data = None
        
        if(not conn.is_connected()):
            messages.error(req,"MongoDB connection failed")
            return render(req,'Upload/HTMX/message.html')

    
        if(f.is_valid()):
            excel_file = req.FILES["file"]
            file_name = f.cleaned_data.get("file_name")
            
            try:
                res = conn.find_one({"data.header.file_name":file_name,"_id":{"$ne":ObjectId(id)}},{"data.header.file_name":1})
                
                if(res):
                    messages.error(req, "File Name already exists. Please choose a different one!")
                    return render(req,'Upload/HTMX/message.html')
                    
                
            except Exception as e:
                APP_LOG.write_error( LogStructure().set_request(req).set_description(type=Task.EXCEPTION,user=req.user,exception=e))    
                messages.error(req,DEFAULT_ERROR)
                return render(req,'Upload/HTMX/message.html')
        
            try:
                with excel_file.open() as file:
                    image_idx, pd_data = image_load(file.read())
                    
                    if(pd_data is None):
                        messages.error(req,"Data Extraction failed")
                        return render(req,'Upload/HTMX/message.html')
                    
                    rows, _ = pd_data.shape
                    pd_data = pd_data.to_json()
                    
            except Exception as e:
                APP_LOG.write_error( LogStructure().set_request(req).set_description(type=Task.EXCEPTION,user=req.user,exception=e))    
                messages.error(req,DEFAULT_ERROR)
                return render(req,'Upload/HTMX/message.html')
            
            template = MongoTemplate().add_post(**get_post_id(req.user)).add_image(image_idx).add_excel(json.loads(pd_data)).add_file(file_name).add_uploader(req.user.id).add_feed(rows)
            
            try:
                exists:dict[str,dict[str,dict|list[dict]]] = conn.find_one({"_id":ObjectId(id)})
                locked = any([i.get('locked') for i in exists.get('data',{}).get('feed',[])])
                
                if(exists is None):
                    messages.error(req, "Record not found!")
                
                elif(locked):
                    messages.error(req,"Data Insertion not possible. Data is locked")
                else:
                    managers = exists.get('header',{}).get('manager',[])
                    template = template.add_manager(managers)
                    success = conn.replace_one({"_id":ObjectId(id)},template)
                    
                    if(success):
                        messages.success(req,"Data Edit successful. Data Updated of Mongo ID:%s" % id)
                    else:
                        messages.error(req,"Data Edit unsuccessful. Data Updation of Mongo ID:%s failed" % id)
                    
                    
            except Exception as e:
                APP_LOG.write_error( LogStructure().set_request(req).set_description(type=Task.EXCEPTION,user=req.user,exception=e))    
                messages.error(req,DEFAULT_ERROR)
                
            finally:
                conn.close()
            
        else:
            messages.error(req, "Invalid form. %s" **f.errors )
        
        return render(req,'Upload/HTMX/message.html')
    
    return HttpResponse(status=403)