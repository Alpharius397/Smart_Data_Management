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
            return render(req,'Excel/index.html',{'form':f,'alert':'MongoDB connection failed'})
        
        if(f.is_valid()):
            excel_file = req.FILES["file"]
            file_name = f.cleaned_data.get("file_name")
        
            with excel_file.open() as file:
                image_idx, pd_data = image_load(file.read())
                
                pd_data = pd_data.to_json()
            
            if(pd_data is None):
                return mongo_setup_failed(req,form=f)
                
            template = MongoTemplate(file_name,pd_data,req.user.username,image_idx).get_json()
            
            res = excel.insert_one(template)
            
            verify = VerificationTable(mongo_id=res.inserted_id,belongs=req.user.uploader)
            verify.save()
            
            
            return render(req,'Excel/index.html',{'form':f,'alert':'Excel Extraction Success'})
        
        return render(req,'Excel/index.html',{'form':f,'alert':'Something Went Wrong'})
        
    else:
        f = ExcelForm(initial={'username':req.user.username})
    
    return render(req,'Excel/index.html',{'form':f})


def image_load(data: bytes) -> tuple[list[int], pd.DataFrame]:
    
    
    pd_data:pd.DataFrame = None
    op_data:op.Workbook = None
    converted:set[int] = set()
    
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
                
                if(j not in converted):
                    pd_data[pd_data.columns[j]] = pd_data[pd_data.columns[j]].astype(str)
                    
                    converted.add(j)
                    
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


def get_image_idx(columns):
    idx = None
    
    for i,j in enumerate(columns):
        if(j.lower()=='image'):
            idx = i
            break
    
    return idx


def owner_view(req: HttpRequest,id) -> HttpResponse:
    if(not ((req.user.is_authenticated) and (is_uploader(req.user)))):
        return redirect(reverse(settings.LOGIN_URL) + '?alert=Unauthenticated Request')
    
    user = req.user.username
    
    excel = MongoConnection(settings.MONGO_URL).connect(settings.MONGO_CRED)
    
    result:dict[str,Any | dict | list] = excel.find_one({"$and":[{"_id":ObjectId(id)},{"belongs":user}]})

    if(result is None):
        return redirect(reverse('Excel:dash')+'?alert=Record not found')
    
    pd_data = pd.read_json(StringIO(result.get('excel','').get('data','')))
    image_idx:list = result.get('excel',{}).get('image',[])
    feedback = result.get('verify',[])
    
    # removing image column cause duh
    available_column = set(pd_data.columns.to_list()) - set([ pd_data.columns[i] for i in image_idx])
    
    column = req.GET.get('column',None)
    value = req.GET.get('search',None)
    
    if((column) and (column not in available_column)):
        return render(req,'Excel/owner.html',{'column':pd_data.columns.to_list(),'result':pd_data.iterrows(),'alert':'Column Not found','feed':feedback})
    
    if(column and (value)):
        sample = pd_data[pd_data[column].astype(str).str.contains(value)]
        
        if(sample.empty):
            return render(req,'Excel/owner.html',{'column':pd_data.columns.to_list(),'result':pd_data.iterrows(),'alert':'Data was not found!','feed':result.get('verify',[])})
        
        pd_data = sample
            
    
    return render(req,'Excel/owner.html',{'column':pd_data.columns.to_list(),'result':pd_data.iterrows(),'feed':result.get('verify',[])})


def assign_view(req: HttpRequest,id) -> HttpResponse:
    if(not ((req.user.is_authenticated) and (is_manager(req.user)))):
        return redirect(reverse(settings.LOGIN_URL) + '?alert=Unauthenticated Request')
    
    user = req.user.username
    
    excel = MongoConnection(settings.MONGO_URL).connect(settings.MONGO_CRED)
    
    result:dict[str,Any | dict | list] = excel.find_one({"$and":[{"_id":ObjectId(id)},{"belongs":user}]})

    if(result is None):
        return redirect(reverse('Excel:dash')+'?alert=Record not found')
    
    pd_data = pd.read_json(StringIO(result.get('excel','').get('data','')))
    image_idx:list = result.get('excel',{}).get('image',[])
    feedback = result.get('verify',[])
    
    # removing image column cause duh
    available_column = set(pd_data.columns.to_list()) - set([ pd_data.columns[i] for i in image_idx])
    
    if(req.method=='GET'):
        column = req.GET.get('column',None)
        value = req.GET.get('search',None)
        f=VerifyForm()
        
        if((column) and (column not in available_column)):
            return render(req,'Excel/assign.html',{'column':pd_data.columns.to_list(),'result':pd_data.iterrows(),'alert':'Column Not found','image':image_idx,'form':f})
        
        if(column and (value)):
            sample = pd_data[pd_data[column].astype(str).str.contains(value)]
            
            if(sample.empty):
                return render(req,'Excel/assign.html',{'column':pd_data.columns.to_list(),'result':pd_data.iterrows(),'alert':'Data was not found!','image':image_idx,'form':f})
            
            pd_data = sample
                
        
        return render(req,'Excel/assign.html',{'column':pd_data.columns.to_list(),'result':pd_data.iterrows(),'image':image_idx,'form':f})

    elif(req.method=='POST'):
    
        f=VerifyForm(req.POST)
        record = VerificationTable.objects.filter(Q(mongo_id=id))
        
        if(len(record)>0):
            return redirect(reverse('Excel:dash')+'?alert=Record not found')
        
        record = record[0]
        
        if(f.is_valid()):
            status = f.cleaned_data.get("status")
            feedback = f.cleaned_data.get("feedback")
            
            if(status=='True'):
                status = True
            elif(status=='False'):
                status = False
            else:
                status = None
            
            record.assigned_status = status
            record.assigned_feedback = feedback
            record.save()
            
            return render(req,'Excel/assign.html',{'column':pd_data.columns,'result':pd_data.iterrows(),'image':image_idx,'form':f,'alert':'Task Submission done'})
            
        else:
            
            return render(req,'Excel/assign.html',{'column':pd_data.columns,'result':pd_data.iterrows(),'image':image_idx,'form':f})
        
