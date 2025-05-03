from django.shortcuts import render
from django.http import HttpRequest, HttpResponse, QueryDict
from Upload.forms import ExcelForm
from Main.models import MongoConnection, MongoTemplate
from Logs.loggers import APP_LOG, LogStructure, DEFAULT_ERROR, Task
from User.models import is_admin, is_authenticated
import json
from bson.objectid import ObjectId
from tools.get_image import image_load
from tools.url_auth import htmx_response, is_auth_get, is_hx_delete, is_hx_post, auth_needed, is_hx_put, login_needed
from User.models import get_post_id
from django.contrib import messages

@login_needed(admin_only=True)
def upload_screen(req:HttpRequest):

    if(is_auth_get(req)):        
        f = ExcelForm(initial={'username':req.user.username})
    
        return render(req,'Upload/upload.html',{'form':f})

@login_needed(admin_only=True)
def edit_screen(req: HttpRequest, id:str) -> HttpResponse:
    
    if(is_auth_get(req)):
        conn = MongoConnection().connect()
        file_name:str = None
        try:
            res = conn.find_one({"_id":ObjectId(id)},{"data.header.file_name":1})
            file_name = MongoConnection.getValue(res, str, "data", "header", "file_name")
        finally:
            conn.close()
            
        f = ExcelForm(initial={'username':req.user.username,'file_name':file_name})
    
        return render(req,'Upload/edit.html',{'form':f,'id':id})

@login_needed(admin_only=True)
def delete_screen(req: HttpRequest, id:str) -> HttpResponse:
    
    if(is_auth_get(req)):
        return render(req,'Upload/delete.html',{'id':id})


@htmx_response
@auth_needed(admin_only=True)
def delete(req: HttpRequest, id:str) -> HttpResponse:
    
    if(is_hx_delete(req)):
        
        conn = MongoConnection().connect()
        result = None
        
        try:
            try:
                result = conn.find_one({'_id':ObjectId(id),"data.excel.feed.locked":{"$ne":True}},{"_id":1})
                
            except Exception as e:
                APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,user=req.user,exception=e))
                messages.error(req,"MongoDB connection failed")
                return render(req,'Upload/HTMX/message.html')
            
            if(result is None):
                messages.error(req,"MongoDB ID %s not found! or, Data is Locked and Deletion not possible!" % id)
                
            else:
                
                try:
                    if(conn.delete_one({"_id":ObjectId(id),"header.uploader":req.user.id})):
                        messages.success(req,"MongoDB ID %s was deleted successfully!" % id)
                    else:
                        messages.error(req,"MongoDB ID %s was not deleted!" % id)
                        
                except Exception as e:
                    APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,user=req.user,exception=e))       
                    messages.error(req,DEFAULT_ERROR)
                
        finally:
            conn.close()    
            
        return render(req,'Upload/HTMX/message.html')

@htmx_response
@auth_needed(admin_only=True)
def upload(req: HttpRequest) -> HttpResponse:

    if(is_hx_post(req)):

        f = ExcelForm(req.POST,req.FILES)
        conn = MongoConnection().connect()
        pd_data = None
        
        if(not conn.is_connected()):
            messages.error(req,"MongoDB connection failed")
            return render(req,'Upload/HTMX/message.html')

        
        try:
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
                    return render(req,'Upload/HTMX/message.html')
                    
                try:
                    with excel_file.open() as file:
                        image_idx, pd_data = image_load(file.read())
                        
                        if(pd_data is None):
                            messages.error(req,"Data Extraction failed")
                            return render(req,'Upload/HTMX/message.html')
                        
                except Exception as e:
                    APP_LOG.write_error( LogStructure().set_request(req).set_description(type=Task.EXCEPTION,user=req.user,exception=e))    
                    messages.error(req,DEFAULT_ERROR)
                    return render(req,'Upload/HTMX/message.html')
                
                template = MongoTemplate().add_post(**get_post_id(req.user)).add_image(image_idx).add_excel(pd_data).add_file(file_name).add_uploader(req.user.id)
                
                try:
                    res = conn.insert_one(template)
                    messages.success(req,"Data Insertion successful. Data inserted with Mongo ID:%s" % res)
                except Exception as e:
                    APP_LOG.write_error( LogStructure().set_request(req).set_description(type=Task.EXCEPTION,user=req.user,exception=e))    
                    messages.error(req,DEFAULT_ERROR)
            else:
                messages.error(req, "Invalid form. %s" % f.errors.as_text())
                
        finally:
            conn.close()
        
        return render(req,'Upload/HTMX/message.html')

@htmx_response
@auth_needed(admin_only=True)
def edit(req: HttpRequest, id:str) -> HttpResponse:

    if(is_hx_post(req)):

        f = ExcelForm(req.POST,req.FILES)
    
        conn = MongoConnection().connect()
        pd_data = None
        
        if(not conn.is_connected()):
            messages.error(req,"MongoDB connection failed")
            return render(req,'Upload/HTMX/message.html')

        try:
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
                        
                except Exception as e:
                    APP_LOG.write_error( LogStructure().set_request(req).set_description(type=Task.EXCEPTION,user=req.user,exception=e))    
                    messages.error(req,DEFAULT_ERROR)
                    return render(req,'Upload/HTMX/message.html')
                
                template = MongoTemplate().add_post(**get_post_id(req.user)).add_image(image_idx).add_excel(pd_data).add_file(file_name).add_uploader(req.user.id)            
                try:
                    exists:dict[str,dict[str,dict|list[dict]]] = conn.find_one({"_id":ObjectId(id),"data.feed.locked":{"$ne":True}})
                    
                    if(exists is None):
                        messages.error(req, "Record was not found or Data is locked!")
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
                    
                
            else:
                messages.error(req, "Invalid form. %s" % f.errors.as_text())
            
        finally:
            conn.close()
            
        return render(req,'Upload/HTMX/message.html')