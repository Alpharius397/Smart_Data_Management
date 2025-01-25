from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from Excel.forms import ExcelForm
from Excel.models import MongoConnection, MongoTemplate, get_error_info
from django.urls import reverse
from django.conf import settings
from User.models import is_uploader, is_authenticated
import json
from bson.objectid import ObjectId
from tools.get_image import image_load
from User.models import get_post
from django.contrib import messages

# Create your views here.
def upload_screen(req:HttpRequest):
    if(not (is_authenticated(req.user) and is_uploader(req.user))):
        return redirect(reverse(settings.LOGIN_URL) + '?alert=Unauthenticated Request')
    
    if(req.method=="GET"):        
        f = ExcelForm(initial={'username':req.user.username})
    
        return render(req,'Upload/upload.html',{'form':f})

def edit_screen(req: HttpRequest) -> HttpResponse:
    if(not (is_authenticated(req.user) and is_uploader(req.user))):
        return redirect(reverse(settings.LOGIN_URL) + '?alert=Unauthenticated Request')
    
    if(req.method=="GET"):        
        f = ExcelForm(initial={'username':req.user.username})
    
        return render(req,'Upload/upload.html',{'form':f})

    
def upload(req: HttpRequest) -> HttpResponse:

    if((is_authenticated(req.user) and is_uploader(req.user)) and req.META.get('HTTP_HX_REQUEST') and (req.method=="POST")):

        f = ExcelForm(req.POST,req.FILES)
    
        connection = MongoConnection(settings.MONGO_URL)
        excel = connection.connect(settings.MONGO_CRED)
        pd_data = None
        
        if(excel is None):
            messages.error(req,"MongoDB connection failed")
            return render(req,'Excel/upload.html',{'form':f,'alert':'MongoDB connection failed'})
    
        if(f.is_valid()):
            excel_file = req.FILES["file"]
            file_name = f.cleaned_data.get("file_name")
        
            with excel_file.open() as file:
                image_idx, pd_data = image_load(file.read())
                
                if(pd_data is None):
                    messages.error(req,"Data Extraction failed")
                    return render(req,'Upload/HTMX/message.html')
                
                rows, _ = pd_data.shape
                pd_data = pd_data.to_json()
            
            template = MongoTemplate().add_post(**get_post(req.user)).add_image(image_idx).add_excel(json.loads(pd_data)).add_file(file_name).add_uploader(req.user.username).add_feed(rows).get_json()
            
            try:
                res = excel.insert_one(template).inserted_id
                messages.success(req,"Data Insertion successful. Data inserted with Mongo ID:%s" % res)
            except Exception as e:
                messages.error(req, "Something went wrong. Error: %s" % get_error_info(e))
            finally:
                connection.connection.close()
        else:
            messages.error(req, "Invalid form. %s" **f.errors )
        
        return render(req,'Upload/HTMX/message.html')

def edit(req: HttpRequest, id:str) -> HttpResponse:

    if((is_authenticated(req.user) and is_uploader(req.user)) and req.META.get('HTTP_HX_REQUEST') and (req.method=="POST")):

        f = ExcelForm(req.POST,req.FILES)
    
        connection = MongoConnection(settings.MONGO_URL)
        excel = connection.connect(settings.MONGO_CRED)
        pd_data = None
        
        if(excel is None):
            messages.error(req,"MongoDB connection failed")
            return render(req,'Excel/upload.html',{'form':f,'alert':'MongoDB connection failed'})
    
        if(f.is_valid()):
            excel_file = req.FILES["file"]
            file_name = f.cleaned_data.get("file_name")
        
            with excel_file.open() as file:
                image_idx, pd_data = image_load(file.read())
                
                if(pd_data is None):
                    messages.error(req,"Data Extraction failed")
                    return render(req,'Upload/HTMX/message.html')
                
                rows, _ = pd_data.shape
                pd_data = pd_data.to_json()
            
            template = MongoTemplate().add_post(**get_post(req.user)).add_image(image_idx).add_excel(json.loads(pd_data)).add_file(file_name).add_uploader(req.user.username).add_feed(rows)
            
            try:
                exists:dict[str,dict[str,dict]] = excel.find_one({"_id":ObjectId(id)})
                
                if(exists is None):
                    messages.error(req, "Record not found!")
                
                else:
                    managers = exists.get('header',{}).get('manager',[])
                    template = template.add_manager(managers)
                    excel.replace_one({"_id":ObjectId(id)},template)
                    
                    messages.success(req,"Data Insertion successful. Data Updated with Mongo ID:%s" % id)
                    
            except Exception as e:
                messages.error(req, "Something went wrong. Error: %s" % get_error_info(e))
                
            finally:
                connection.connection.close()
            
        else:
            messages.error(req, "Invalid form. %s" **f.errors )
        
        return render(req,'Upload/HTMX/message.html')