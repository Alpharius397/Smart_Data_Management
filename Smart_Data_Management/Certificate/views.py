from django.shortcuts import render
from django.http import HttpRequest, HttpResponse, JsonResponse
from Main.models import MongoConnection
from django.conf import settings
from User.models import get_post_id, get_user_by_id, is_authenticated, is_admin, is_manager, get_manager_by_name, get_admin_by_name, Admin, Manager
from tools.url_auth import *
from tools.encrypt import decrypt_data
from tools.get_image import expand_image
import typing
import re
from Main.models import *
from Logs.loggers import APP_LOG, LogStructure, DEFAULT_ERROR, Task
from tools.token import get_token, hash_token
from django.views.decorators.csrf import csrf_exempt
from Card.models import Card
from pymongo.collection import ObjectId
from django.utils import timezone
from datetime import datetime
import json
from Crypto.Hash import SHA256
import pandas as pd

VIEW_DATA = {"_id":1,"header.manager":1,"header.uploader":1,"data.header.file_name":1}
READ_TOKEN:str = "read-token"
LOADING:str = "Loading"
DONE:str = "Done"
CARD_DATA:str = "Data"
ERROR_JSON:dict[str, str] = {"info":"Unauthenticated Request","status":False}

class ReportStructure(typing.NamedTuple):
    profile_img:str
    personal_info:dict[str,str]
    sem_data:dict[str,dict[str,str]]

class Certificate(typing.NamedTuple):
    certificateHash : str
    timePeriod : timezone.datetime

def getMongoID(cardID: str) -> tuple[str, int] | None:
    try:
        card =  Card.objects.get(cardID=cardID)
        return card.mongoID, card.rowIndex
    
    except:
        return None

def getCertificateData(certificate: str) -> Certificate | None:
    try:
        certiHash, time = certificate.split(":")
        
        time = datetime(2025,1,1,tzinfo=timezone.get_current_timezone()).fromisoformat(time)
        
        return Certificate(certificateHash=certiHash, timePeriod=time)

    except:
        return None

def getData(pds: pd.DataFrame, idx:int) -> dict | None:
    try:
        return pds.iloc[[idx]].to_dict()
    except:
        return None
    
def getSHA(data: str) -> str:
    Hash = SHA256.new(data.encode())
    return Hash.hexdigest()


def certificate_check(req :HttpRequest, certificate: str, cardID:str) -> HttpResponse:
    """ certificate is sha256 encoding of data, cardID is cardID """
    
    if(not (is_authenticated(req.user))):
        return auth_needed(req)
    
    if(is_auth_get(req)):
        
        mongoID, row = getMongoID(cardID)
        
        if(mongoID is None):
            return render(req, "Certificate/HTMX/error.html", context={"error":"No such card was not found"})
        
        conn = MongoConnection().connect()
        info = getCertificateData(certificate)
        
        if(info is None):
            return render(req, "Certificate/HTMX/error.html", context={"error":"Invalid Certificate Credentials"})
        
        if(datetime().now(tz=timezone.get_current_timezone())>info.timePeriod):
            return render(req, "Certificate/HTMX/error.html", context={"error":"Certificate Expired!"})        
        
        record = conn.find_one({"_id":ObjectId(mongoID)},{"data.excel":1})
        pd_data = getData(pd.DataFrame(record.get('data',{}).get('excel',{})),row)
        
        if(pd_data is None):
            return render(req, "Certificate/HTMX/error.html", context={"error":"Data Loading Failed!"})
        
        if(getSHA(json.dumps(pd_data))!=info.certificateHash):
            return render(req, "Certificate/HTMX/error.html", context={"error":"Invalid Certificate Credentials"})
        
        if(record is None):
            return render(req, "Certificate/HTMX/error.html", context={"error":"MongoID found!"})
        
        profile_img = r'^Profile_Image$'
        sem_data = r'.+Sem_(\d+)$'
        
        result, header = record.get('data',{}), record.get('header',{})
        
        columns = record.keys()
        
        profile_col = [i for i in columns if re.match(profile_img,i)]
        sem_col = [i for i in columns if re.match(sem_data,i)]
        personal_col = [i for i in columns if((i not in profile_col) and (i not in sem_col))]
        
        sem_dict:dict[str,list[str]] = {}
        
        profile_col = profile_col[0] if profile_col else None
        
        
        wid, hei, data = result[profile_col].split(":")

        result[profile_col] = expand_image(width=int(wid),height=int(hei),img_data=data)
        for i in sem_col:
            sem:list[str] = re.findall(sem_data,i)
            
            if(sem):
                sem = sem[0]
                if(sem not in sem_dict): sem_dict[sem] = list()
                sem_dict[sem].append(i)

        view = ReportStructure(profile_img=profile_col,personal_info=personal_col,sem_data=sem_dict)
        context = {'data':result,'personal':view.personal_info,'pic':view.profile_img,'sem_dict':view.sem_data,**header}

        return render(req, "Certificate/HTMX/certificate.html", context=context)
        
    return HttpResponse(status=403)