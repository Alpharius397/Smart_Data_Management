from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from Excel.forms import ExcelForm,VerifyForm
from django.db.models import Q
from Main.tools import *
from Excel.models import VerificationTable,MongoConnection,VERIFY_COUNT,MongoTemplate
from django.urls import reverse
from django.conf import settings
from User.models import is_manager, is_uploader
import pandas as pd
from io import BytesIO,StringIO
from typing import Any
import json
import openpyxl as op
from bson.objectid import ObjectId
from tools.get_image import get_image_data
from Excel.templatetags.bad_image import bad_image
from tools.get_image import compress_image
from tools.encrypt import encrypt_data,decrypt_data
from base64 import b64encode, b64decode


def mongo_setup_failed(req, **kwargs):
    context = {'alert':'Excel Sheet is empty or MongoDB connection failed'}
    context.update(kwargs)
    return render(req,'Excel/index.html',context)


# Create your views here.
def upload_screen(req:HttpRequest):
    if(not ((req.user.is_authenticated) and (is_uploader(req.user)))):
        return redirect(reverse(settings.LOGIN_URL) + '?alert=Unauthenticated Request')
    
    if(req.method=="POST"):
        f = ExcelForm(req.POST,req.FILES)
        
        connection = MongoConnection(settings.MONGO_URL)
        excel = connection.connect(settings.MONGO_CRED)
        pd_data = None
        
        if(excel is None):
            return render(req,'Excel/upload.html',{'form':f,'alert':'MongoDB connection failed'})
        
        if(f.is_valid()):
            excel_file = req.FILES["file"]
            file_name = f.cleaned_data.get("file_name")
        
            with excel_file.open() as file:
                image_idx, pd_data = image_load(file.read())
                rows, _ = pd_data.shape
                pd_data = pd_data.to_json()
            
            if(pd_data is None):
                return mongo_setup_failed(req,form=f)
            
            verify_idx = {str(i):None for i in range(rows)}
            feedback_idx = {str(i):"" for i in range(rows)}
            
            template = MongoTemplate(file_name,json.loads(pd_data),req.user.username,verify_idx,feedback_idx,image_idx).get_json()
            res = excel.insert_one(template)
            
            verify = VerificationTable(mongo_id=res.inserted_id,belongs=req.user.uploader)
            verify.save()
            
            
            return render(req,'Excel/upload.html',{'form':f,'alert':'Excel Extraction Success'})
        
        return render(req,'Excel/upload.html',{'form':f,'alert':'Something Went Wrong'})
        
    else:
        f = ExcelForm(initial={'username':req.user.username})
    
    return render(req,'Excel/upload.html',{'form':f})


def image_load(data: bytes) -> tuple[list[str], pd.DataFrame]:
    
    pd_data:pd.DataFrame = None
    op_data:op.Workbook = None
    converted:set[str] = set()
    
    try:
        pd_data = pd.read_excel(BytesIO(data))
        op_data = op.load_workbook(BytesIO(data))
    except:
        return converted, pd_data
        

    if(op_data and len(op_data.sheetnames)==0):
        return converted, pd_data
        

    op_sheet = op_data[op_data.sheetnames[0]]
    image = get_image_data(op_sheet)
    
    for i, row in pd_data.iterrows():
        for j, col in enumerate(row):
            if((i+1,j) in image):
                
                if(pd_data.columns[j] not in converted):
                    pd_data[pd_data.columns[j]] = pd_data[pd_data.columns[j]].astype(str)
                    
                    converted.add(pd_data.columns[j])
                    
                pd_data.iat[i,j] = image[(i+1,j)]
                    
    return list(converted), pd_data
        

def dash_board(req: HttpRequest) -> HttpResponse:
    if(not ((req.user.is_authenticated) and (is_uploader(req.user) or is_manager(req.user)))):
        return redirect(reverse(settings.LOGIN_URL) + '?alert=Unauthenticated Request')
    
    user = req.user
    username = req.user.username
    
    excel = MongoConnection(settings.MONGO_URL).connect(settings.MONGO_CRED)
    
    if(excel is None):
        return mongo_setup_failed(req)
    
    verify:list = None
    upload:list = None
    
    available_id = [ ObjectId(i.mongo_id) for i in VerificationTable.objects.only('mongo_id')]
    
    if(is_manager(user)):
        verify = excel.find({"_id":{"$in":available_id},"verify.user":{"$eq":username}}).to_list()
        
    elif(is_uploader(user)):
        upload = excel.find({"_id":{"$in":available_id},"belongs":{"$eq":username}}).to_list()
        
    return render(req,'Excel/dash.html',{'upload':upload,'verify':verify})


def data_view(req: HttpRequest,id) -> HttpResponse:
    if(not ((req.user.is_authenticated) and (is_uploader(req.user) or is_manager(req.user)))):
        return redirect(reverse(settings.LOGIN_URL) + '?alert=Unauthenticated Request')
    
    user = req.user.username
    
    excel = MongoConnection(settings.MONGO_URL).connect(settings.MONGO_CRED)
    
    result:dict[str,Any | dict | list] = excel.find_one({"$and":[{"_id":ObjectId(id)},{"$or":[{"belongs":req.user.username},{"verify.user":req.user.username}]}]})

    if(result is None):
        return redirect(reverse('Excel:dash')+'?alert=Record not found')

    pd_data = pd.DataFrame(result.get('excel',{}).get('data',{}))
    image_idx:list = result.get('excel',{}).get('image',[])

    # removing image column cause duh
    available_column = set(pd_data.columns.to_list()) - set([ i for i in image_idx])    
    
    return render(req,'Excel/view.html',{'column':available_column,})


def search_query(pd_data:pd.DataFrame,column:str,value,available_column):
    
    if((column and value) and (column in available_column) and (column in pd_data.columns)):
        sample = pd_data[pd_data[column].astype(str).str.contains(value)]
        return sample
    
    return pd_data
        
def table_query(req: HttpRequest, id:str):
    if(req.method=='GET' and req.META.get('HTTP_HX_REQUEST') and (req.user.is_authenticated)):
        column = req.GET.get('column',None)
        value = req.GET.get('search',None)
        
        excel = MongoConnection(settings.MONGO_URL).connect(settings.MONGO_CRED)
    
        result:dict[str,Any | dict | list] = excel.find_one({"$and":[{"_id":ObjectId(id)},{"$or":[{"belongs":req.user.username},{"verify.user":req.user.username}]}]})
        
        pd_data = pd.DataFrame(result.get('excel',{}).get('data',{}))
        image_idx:list = result.get('excel',{}).get('image',[])
        verify_idx:list = result.get('excel',{}).get('verify',{})
        
        available_column = set(pd_data.columns.to_list()) - set([ i for i in image_idx])
        
        pd_data = search_query(pd_data,column,value,available_column)
        
        return render(req,'HTMX/table.html',{'column':pd_data.columns,'result':pd_data.iterrows(),'image':image_idx,'verify':verify_idx})
    
    
def verify_page(req: HttpRequest, id:str, index:int) -> HttpResponse:
    if(not (req.user.is_authenticated)):
        return redirect(reverse(settings.LOGIN_URL) + '?alert=Unauthenticated Request')
    
    excel = MongoConnection(settings.MONGO_URL).connect(settings.MONGO_CRED)

    result:dict[str,Any | dict | list] = excel.find_one({"$and":[{"_id":ObjectId(id)},{"$or":[{"belongs":req.user.username},{"verify.user":req.user.username}]}]})
    
    pd_data = pd.DataFrame(result.get('excel',{}).get('data',{}))
    image_idx:list = result.get('excel',{}).get('image',[])
    manager:str = result.get('verify',[])
    verify_idx = result.get('excel',{}).get('verify',{})
    feed_idx = result.get('excel',{}).get('feedback',{})
    
    if(int(index)>pd_data.shape[0]):
        return redirect(reverse('Excel:assign_view',args={'id':id}) + '?alert=Index not found!')
    
    data = pd_data.iloc[int(index)].to_dict()
    context = {'id':id,'data':data,'image':image_idx,'column':pd_data.columns}
    
    if(req.method=='POST'):
        f = VerifyForm(req.POST)
        
        if(f.is_valid()):
            status, feed = f.cleaned_data.get("status"), f.cleaned_data.get("feedback") 
            
            if(status=='True'):
                status = True
            elif(status=='False'):
                status = False
            else:
                status = None
                
            verify_idx[str(index)] = status
            feed_idx[str(index)] = feed
            
            excel.update_one({"_id":ObjectId(id)},{"$set":{"excel.verify":verify_idx,'excel.feedback':feed_idx}})
    
    if(is_uploader(req.user)):
        if(manager is not None):
            context.update({'manager':[{'user':i.get('user',None),'status':verify_idx[str(index)],'feedback':feed_idx[str(index)]} for i in manager]})
            
        return render(req,'Excel/user/uploader.html',context=context)
    
    else:
        context.update({'form':VerifyForm(initial={'status':verify_idx[str(index)],'feed':feed_idx[str(index)]})})
        return render(req,'Excel/user/manager.html',context=context)

def single_query(req: HttpRequest, id:str, index:int):
    if(req.method=='GET' and req.META.get('HTTP_HX_REQUEST') and (req.user.is_authenticated)):
        column = req.GET.get('column',None)
            
        excel = MongoConnection(settings.MONGO_URL).connect(settings.MONGO_CRED)

        result:dict[str,Any | dict | list] = excel.find_one({"$and":[{"_id":ObjectId(id)},{"$or":[{"belongs":req.user.username},{"verify.user":req.user.username}]}]})

        pd_data = pd.DataFrame(result.get('excel',{}).get('data',{}))
        image_idx:list = result.get('excel',{}).get('image',[])

        if(int(index)>pd_data.shape[0]):
            return redirect(reverse('Excel:assign_view',args={'id':id}) + '?alert=Index not found!')

        if(column):
            data = pd_data.iloc[int(index)][[column]].to_dict()
        else:
            data = pd_data.iloc[int(index)].to_dict()
            
        return render(req,'HTMX/single_table.html',context={'id':id,'data':data,'image':image_idx,'column':pd_data.columns})

def compress_data(req: HttpRequest, id:str, index:int):
    excel = MongoConnection(settings.MONGO_URL).connect(settings.MONGO_CRED)

    result:dict[str,Any | dict | list] = excel.find_one({"$and":[{"_id":ObjectId(id)},{"$or":[{"belongs":req.user.username},{"verify.user":req.user.username}]}]})

    pd_data = pd.DataFrame(result.get('excel',{}).get('data',{}))
    image_idx:list = result.get('excel',{}).get('image',[])

    if(int(index)>pd_data.shape[0]):
        return redirect(reverse('Excel:assign_view',kwargs={'id':id}) + '?alert=Index not found!')


    data = pd_data.iloc[int(index)].to_dict()
    
    for i in image_idx:
        img_data = data[i]
        
        raw_img = img_data.split(':')
    
        try:
            width, height, img = raw_img
        except:
            width, height = 100,100
            img = bad_image
            
        img = compress_image(BytesIO(b64decode(img)))
        
        data[i] = img
        
    
    with open('/home/omnissiah/Project/nodejs/react/Smart_Data_Management/Smart_Data_Management/Excel/asd.txt','w') as f:
        f.write(encrypt_data(settings.KEY,data))
    print(decrypt_data(settings.KEY,encrypt_data(settings.KEY,data)))
    return redirect(reverse('Excel:single',kwargs={'id':id,'index':index}))
    
            