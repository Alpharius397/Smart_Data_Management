from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from Excel.forms import ExcelForm,VerifyForm
from django.db.models import Q
from Main.tools import *
from Excel.models import VerificationTable,MongoConnection,VERIFY_COUNT
from django.urls import reverse
from django.conf import settings
from Main.views import is_manager, is_uploader
import pandas as pd
from io import BytesIO,StringIO
from typing import Any
import json
import openpyxl as op
from bson.objectid import ObjectId
from tools.get_image import get_image_data
from base64 import b64encode, b64decode
from PIL import Image

class MongoTemplate:
        
    def __init__(self, file_name:str ,data:dict[str,Any], belongs:str) -> None:
        
        self.excel = {'data':data,'name':file_name}
        self.belongs = belongs
        self.verify = []

    def get_json(self):
        
        to_get = ['excel','belongs','verify']
        
        return {i:self.__getattribute__(i) for i in to_get}
        

def mongo_setup_failed(req, **kwargs):
    context = {'alert':'MongoDB connection failed'}
    context.update(kwargs)
    return render(req,'Excel/index.html',context)


# Create your views here.
def upload_screen(req:HttpRequest):
    if(not ((req.user.is_authenticated) and (is_uploader(req.user)))):
        return redirect(reverse(settings.LOGIN_URL) + '?alert=Unauthenticated Request')
    
    user = req.user.username
    
    connection = MongoConnection(settings.MONGO_URL)
    excel = connection.connect(settings.MONGO_CRED)
    pd_data = None
    
    if(excel is None):
        return render(req,'Excel/index.html',{'form':f,'alert':'MongoDB connection failed'})

    if(req.method=="POST"):
        f = ExcelForm(req.POST,req.FILES)
        
        if(f.is_valid()):
            excel_file = req.FILES["file"]
            file_name = f.cleaned_data.get("file_name")
        
            with excel_file.open() as file:
                pd_data = image_load(file.read()).to_json()
            
            if(pd_data is None):
                return mongo_setup_failed(req,form=f)
                
            template = MongoTemplate(file_name,pd_data,user).get_json()
            
            res = excel.insert_one(template)
            
            verify = VerificationTable(mongo_id=res.inserted_id,belongs=req.user.uploader)
            verify.save()
            
            
            return render(req,'Excel/index.html',{'form':f,'alert':'Excel Extraction Success'})
        
        return render(req,'Excel/index.html',{'form':f,'alert':'Something Went Wrong'})
        
    else:
        f = ExcelForm(initial={'username':req.user.username})
    
    return render(req,'Excel/index.html',{'form':f})

def image_load(data: bytes) -> pd.DataFrame:
    pd_data = pd.read_excel(BytesIO(data))
    op_data = op.load_workbook(BytesIO(data))
    
    # Do something about this
    # if(len(op_data.sheetnames)==0):
    #     raise ValueError("empty excel")
    
    op_sheet = op_data[op_data.sheetnames[0]]
    image = get_image_data(op_sheet)
    
    converted:set[int] = set()
    
    for i, row in pd_data.iterrows():
        for j, col in enumerate(row):
            if((i+1,j) in image):
                
                if(j not in converted):
                    pd_data[pd_data.columns[j]] = pd_data[pd_data.columns[j]].astype(str)
                    
                    converted.add(j)
                    
                pd_data.iat[i,j] = image[(i+1,j)]
                
    print(pd_data)
    
    return pd_data
        

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

def owner_view(req: HttpRequest,id) -> HttpResponse:
    if(not ((req.user.is_authenticated) and (is_uploader(req.user)))):
        return redirect(reverse(settings.LOGIN_URL) + '?alert=Unauthenticated Request')
    
    user = req.user.username
    
    excel = MongoConnection(settings.MONGO_URL).connect(settings.MONGO_CRED)
    
    result = excel.find_one({"$and":[{"_id":ObjectId(id)},{"belongs":user}]})

    if(result is None):
        return redirect(reverse('Excel:dash')+'?alert=Record not found')
    
    pd_data = pd.read_json(StringIO(result['excel']['data']))
    
    idx = None
    
    for i,j in enumerate(pd_data.columns):
        if(j.lower()=='image'):
            idx=i
            break
    
    if(idx is not None):
        for i,row in pd_data.iterrows():
            img_raw:str = row[idx]
            
            pd_data.iat[i,idx] = f"<img src='data:image/jpeg;base64,{img_raw.replace('\\','')}' width=200 height=200>"
            

    
    column = req.GET.get('column',None)
    value = req.GET.get('search',None)
    
    if((column) and (column not in pd_data.columns.to_list())):
        return render(req,'Excel/owner.html',{'column':pd_data.columns,'result':pd_data.iterrows(),'alert':'Column Not found','feed':result.get('verify',[])})
    
    if(column and (value)):
        sample = pd_data[pd_data[column].astype(str).str.contains(value)]
        
        if(sample.empty):
            return render(req,'Excel/owner.html',{'column':pd_data.columns,'result':pd_data.iterrows(),'alert':'Data was not found!','feed':result.get('verify',[])})
        
        pd_data = sample
            
    
    return render(req,'Excel/owner.html',{'column':pd_data.columns,'result':pd_data.iterrows(),'feed':result.get('verify',[])})


def assign_view(req: HttpRequest,id) -> HttpResponse:
    if(not ((req.user.is_authenticated) and (is_manager(req.user)))):
        return redirect(reverse(settings.LOGIN_URL) + '?alert=Unauthenticated Request')
    
    user = req.user.username
    
    excel = MongoConnection(settings.MONGO_URL).connect(settings.MONGO_CRED)
    
    result = excel.find_one({"$and":[{"_id":ObjectId(id)},{"verify.user":{"$eq":user}}]})
    

    if(result is None):
        return redirect(reverse('Excel:dash')+'?alert=Record not found')
    
    
    pd_data = pd.read_json(StringIO(result['excel']['data']))
    
    idx = None
    
    for i,j in enumerate(pd_data.columns):
        if(j.lower()=='image'):
            idx=i
            break
    
    if(idx is not None):
        for i,row in pd_data.iterrows():
            img_raw:str = row[idx]
            
            pd_data.iat[i,idx] = f"<img src='data:image/jpeg;base64,{img_raw.replace('\\','')}' width=200 height=200>"
            
    
    column = req.GET.get('column','')
    value = req.GET.get('search','')
    
    record = VerificationTable.objects.filter(Q(mongo_id=id))[0]
    idx = record.get_user(req.user.manager)
    
    other_feed = [{'user':record.get("verify_%s" % (i), "").__str__(),'status':record.get("verify_%s_status" % (i),""),'feedback':record.get("verify_%s_feedback" % (i),"")} for i in range(1,VERIFY_COUNT+1) if(i!=idx)]
    print(other_feed)
    f=VerifyForm(initial={'status':record.get("verify_%s_status" % (idx),""),'feedback':record.get("verify_%s_feedback" % (idx),"")})
    
    if((column) and (column not in pd_data.columns)):
        return render(req,'Excel/assign.html',{'column':pd_data.columns,'result':pd_data.iterrows(),'alert':'Column Not found','form':f,'other':other_feed})
    
    if(column and (value)):
        sample = pd_data[pd_data[column].astype(str).str.contains(value)]
        
        if(sample.empty):
            return render(req,'Excel/assign.html',{'column':pd_data.columns,'result':pd_data.iterrows(),'alert':'Data was not found!','form':f,'other':other_feed})
        
        pd_data = sample
    
    if(idx is None): return redirect(reverse('Excel:dash')+'?alert=Not authorized for this task')
    
    if(req.method=='POST'):
        f=VerifyForm(req.POST)
        
        if(f.is_valid()):
            status = f.cleaned_data.get("status")
            feedback = f.cleaned_data.get("feedback")
            
            
            if(status=='True'):
                status = True
            elif(status=='False'):
                status = False
            else:
                status = None
            
            record.set_verify(idx,status,feedback)
            
            record.save()
            return render(req,'Excel/assign.html',{'column':pd_data.columns,'result':pd_data.iterrows(),'form':f,'alert':'Task Submission done','other':other_feed})
            
            
    
    else:
        
        return render(req,'Excel/assign.html',{'column':pd_data.columns,'result':pd_data.iterrows(),'form':f,'other':other_feed})
        
