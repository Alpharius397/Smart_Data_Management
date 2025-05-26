from django.shortcuts import render # type: ignore
from django.http import HttpRequest, HttpResponse # type: ignore
from Upload.forms import ExcelForm
from Main.models import Document, MongoConnection, MongoTemplate
from Logs.loggers import APP_LOG, LogStructure, Task
from constants.constants import *
from bson.objectid import ObjectId
from tools.get_image import image_load
from tools.url_auth import htmx_response, is_auth_get, is_hx_delete, is_hx_post, auth_needed, is_hx_put, login_needed
from User.models import get_post_id
from .models import UploadTable, AssignTable, DataTable
from University.models import Subject
from django.contrib import messages # type: ignore
import pandas as pd
from tools.utils import processSubjects, SubjectsNotDefined
from .errors import *

@login_needed(admin_only=True)
def upload_screen(req:HttpRequest):

    if(is_auth_get(req)):        
        f = ExcelForm(initial={'username':req.user.username})
    
        return render(req,'Upload/upload.html',{'form':f})

@login_needed(admin_only=True)
def edit_screen(req: HttpRequest, id:int) -> HttpResponse:
    
    if(is_auth_get(req)):
        context = {'id': id, 'form':ExcelForm()}
        
        
        try:
            file_name = UploadTable.objects.get(id=id).fileName
            context['form'] = ExcelForm(initial={'username':req.user.username,'file_name':file_name})

        except UploadTable.DoesNotExist as e:
            messages.error(req, FileDoesNotExists(id).get_error())
        
        except Exception as f:
            APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,user=req.user,exception=f))       
            messages.error(req, DEFAULT_ERROR)
            
    
        return render(req,'Upload/edit.html',context=context)

@login_needed(admin_only=True)
def delete_screen(req: HttpRequest, id:int) -> HttpResponse:
    if(is_auth_get(req)):
        
        context = {'id': id}
        
        try:
            exists = UploadTable.objects.filter(id=id).only("id").exists()
        
            if(not exists):
                raise FileDoesNotExists(id)
        
        except FileDoesNotExists as e:
            messages.error(req, e.get_error())
        
        except Exception as f:
            APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,user=req.user,exception=f))       
            messages.error(req, DEFAULT_ERROR)
        
        return render(req,'Upload/delete.html',context)


@htmx_response
@auth_needed(admin_only=True)
def delete(req: HttpRequest, id:int) -> HttpResponse:
    
    if(is_hx_delete(req)):
        
        try:
            file = UploadTable.objects.filter(id=id, data__locked=True).only("id")
            
            if(not file.exists()):
                raise FileLocked(id)
                
            else:
                file[0].delete()
                messages.success(req, "File was deleted successfully")
        
        except FileLocked as e:
            messages.error(req, e.get_error())
        
        except Exception as f:
            APP_LOG.write_error(LogStructure().set_request(req).set_description(type=Task.EXCEPTION,user=req.user,exception=f))       
            messages.error(req,DEFAULT_ERROR)
        
        return render(req,'Upload/HTMX/message.html')

@htmx_response
@auth_needed(admin_only=True)
def upload(req: HttpRequest) -> HttpResponse:

    if(is_hx_post(req)):

        form = ExcelForm(req.POST,req.FILES)
        pd_data:pd.DataFrame = pd.DataFrame()
        image_idx:list[int] = []
        post = get_post_id(req.user)
        
        try:
            if(not form.is_valid()):
                raise InvalidForm()
            
            excel_file = req.FILES["file"]
            file_name:str = form.cleaned_data.get("file_name")
            
            if(UploadTable.objects.filter(fileName=file_name).exists()):
                raise FileNameExists()
            
            with excel_file.open() as file:
                image_idx, pd_data = image_load(file.read())
                
                if(pd_data.empty):
                    raise FileProcessFailed()
            
            branchSubjects = Subject.objects.filter(branch__id=post["branch"]).values("name", "semester")

            if(not branchSubjects.exists()):
                raise SubjectsNotDefined(post["branch"])

            pd_data.rename(processSubjects(branchSubjects.iterator(), list(pd_data.columns), image_idx))
            
            fields = pd_data.columns
            fileObj = UploadTable.objects.create(fileName=file_name, uploader=req.user)
            
            rows:list[DataTable] = []
            for row in pd_data.itertuples(index=False):
                rowJson = { fields[idx]:row[idx] for idx in range(len(row))}
                rows.append(DataTable(fileID=fileObj, data=rowJson))
            
            DataTable.objects.bulk_create(rows)
            
        except ValueError as e:
            messages.error(req, FileProcessFailed().get_error())
        
        except InvalidForm as e:
            for _, errors in form.errors:
                for error in errors:
                    messages.error(req, error)
        
        except FileNameExists as f:
            messages.error(f.get_error())
            
        except SubjectsNotDefined as g:
            messages.error(g.get_error())
        
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
                    
                    if(res and res.data.header.file_name):
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
                    exists:Document|None = conn.find_one({"_id":ObjectId(id),"data.feed.locked":{"$ne":True}},{"header":1})
                    
                    if(exists is None):
                        messages.error(req, "Record was not found or Data is locked!")
                    else:
                        template = template.add_manager(exists.header.manager)
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