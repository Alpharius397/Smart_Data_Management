from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from Main.models import MongoConnection
from User.models import is_authenticated
from tools.url_auth import *
from tools.get_image import expand_image
import typing
import re
from Card.models import Card
from pymongo.collection import ObjectId
import json
from Crypto.Hash import SHA256
import pandas as pd
from tools.get_image import compress_image
from Main.templatetags.bad_image import bad_image
from base64 import b64decode
from io import BytesIO
from User.models import get_post_by_ID
from tools.encrypt import monthYearHash

class ReportStructure(typing.NamedTuple):
    profile_img:str
    personal_info:dict[str,str]
    sem_data:dict[str,dict[str,str]]

class Certificate(typing.NamedTuple):
    certificateHash : str
    valid : bool

def getMongoID(cardID: str) -> tuple[str, int] | None:
    try:
        card =  Card.objects.get(cardID=cardID)
        return card.mongoID, card.rowIndex
    
    except:
        return None


def getCertificateData(certificate: str) -> Certificate | None:
    try:
        time, certiHash = certificate[:64], certificate[64:]
                
        timeValid = bool(time==monthYearHash())
            
        return Certificate(certificateHash=certiHash, valid=timeValid)

    except:
        return None

def getData(pds: dict[str,dict[str,dict]], idx:int) -> str | None:
    try:
        pd_data = pd.DataFrame(pds.get('data',{}).get('excel',{}))
        image_idx:list = pds.get('data',{}).get('header',{}).get('image_column',[])
        data = pd_data.iloc[idx].to_dict()

        for i in image_idx:
            img_data = data[i]
            raw_img = img_data.split(':')
        
            try:
                _, _, img = raw_img
            except:
                img = bad_image

            img = compress_image(BytesIO(b64decode(img)))
            data[i] = img
            
        return json.dumps(data)
    except:
        return None
    
def getActualData(pds: dict[str,dict[str,dict]], idx:int) -> dict | None:
    try:
        pd_data = pd.DataFrame(pds.get('data',{}).get('excel',{}))
        data = pd_data.iloc[idx].to_dict()
        header = get_post_by_ID(**pds.get('header',{}).get("post",{}))
        return {"data":data,"header":header}
    except:
        return None
    
def getSHA(data: str) -> str|None:
    try:
        Hash = SHA256.new(data.encode())
        return Hash.hexdigest()
    except Exception as e:
        return None

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

        if(not info.valid):
            return render(req, "Certificate/HTMX/error.html", context={"error":"Certificate Expired!"})        
        
        record = conn.find_one({"_id":ObjectId(mongoID)})
        checkData = getData(record,row)
        pd_data = getActualData(record, row)
        
        if(record is None):
            return render(req, "Certificate/HTMX/error.html", context={"error":"MongoID not found!"})
        
        if((checkData is None) or (info.certificateHash is None)):
            return render(req, "Certificate/HTMX/error.html", context={"error":"Data Loading Failed!"})
        
        if((getSHA(checkData)!=info.certificateHash)):
            return render(req, "Certificate/HTMX/error.html", context={"error":"Invalid Certificate Credentials"})
        
        
        profile_img = r'^Profile_Image$'
        sem_data = r'.+Sem_(\d+)$'
        
        result, header = pd_data.get('data',{}), pd_data.get('header',{})
        
        columns = result.keys()

        profile_col = [i for i in columns if re.match(profile_img,i)]
        sem_col = [i for i in columns if re.match(sem_data,i)]
        personal_col = [i for i in columns if((i not in profile_col) and (i not in sem_col))]

        sem_dict:dict[str,list[str]] = {}
        profile_col = profile_col[0] if profile_col else None
        
        if(profile_col is None):
            result["Profile_Image"] = f"200:200:{bad_image}"
            
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

def loadCertificate(req :HttpRequest, certificate: str, cardID:str) -> HttpResponse:
    if(req.method=="GET"):
        context = {"certificate":certificate, "cardID":cardID, 'auth': False}
        if(is_authenticated(req.user)):
            context['auth'] = True
            
        return render(req,"Certificate/index.html",context=context)