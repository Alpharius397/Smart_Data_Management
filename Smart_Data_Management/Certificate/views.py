from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from Main.models import Document, MongoConnection, MongoTemplate
from Logs.loggers import APP_LOG
from constants.constants import ReportStructure
from View.views import auth_view
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
from tools.encrypt import b64decode, authTokenCheck
from io import BytesIO
from User.models import get_post_by_ID

class Certificate(typing.NamedTuple):
    certificateHash : str
    valid : bool

def getMongoID(cardID: str) -> tuple[str, int] | tuple[None, None]:
    try:
        card =  Card.objects.get(cardID=cardID)
        return card.mongoID, card.rowIndex
    
    except:
        return None, None


def getCertificateData(certificate: str) -> Certificate | None:
    try:
        time, certiHash = certificate[:-64], certificate[-64:]
        timeValid = authTokenCheck(time, False)
            
        return Certificate(certificateHash=certiHash, valid=timeValid)

    except Exception as e:
        print(APP_LOG.get_error_info(e))
        return None

def getSHA(data: str) -> str|None:
    try:
        Hash = SHA256.new(data.encode())
        return Hash.hexdigest()
    except Exception as e:
        return None

@htmx_response
def certificate_check(req :HttpRequest, certificate: str, cardID:str) -> HttpResponse:
    """ certificate is sha256 encoding of data, cardID is cardID """
    
    if(is_hx_get(req)):
        
        mongoID, idx = getMongoID(cardID)
        context:dict[str, list[str] | str | dict[str, typing.Any]] = {}
        
        if(mongoID is None):
            return render(req, "Certificate/HTMX/error.html", context={"error":"No such card was not found"})
        
        conn = MongoConnection().connect()
        info = getCertificateData(certificate)

        if(info is None):
            return render(req, "Certificate/HTMX/error.html", context={"error":"Invalid Certificate Credentials"})

        if(not info.valid):
            return render(req, "Certificate/HTMX/error.html", context={"error":"Certificate Expired!"})        
        
        
        try:
            conditions, filters = MongoTemplate.merge_everything(MongoTemplate.get_buffer_query({"$and":[{"_id":ObjectId(mongoID),"$or":auth_view(req.user)}]}, idx))
            mongoDoc:Document|None = conn.find_one(conditions, filters)
            
            if(mongoDoc is None):
                context['error'] = "Mongo ID %s and index %s not found!" % (mongoID,idx)
                return render(req, "Certificate/HTMX/error.html", context=context)
            
            columns:list = mongoDoc.data.header.columns
            
            if(not ((mongoDoc.data.excel) and (columns) and (mongoDoc.data.header.image_columns))):
                return render(req, "Certificate/HTMX/error.html", context={"error":"MongoID not found!"})
                
            pd_data:dict[str, str | int] = {columns[idx%len(columns)]:i for idx,i in enumerate(mongoDoc.data.excel[0].row)}
            
            for i in mongoDoc.data.header.image_columns:
        
                try:
                    assert (i>=0 and i<len(columns)), "Index checking"
                    img_data = pd_data[columns[i]]
                    assert isinstance(img_data,str), "Image needs to be string"
                    
                    raw_img = img_data.split(':')
                    _, _, img = raw_img
                except Exception as e:
                    img = bad_image

                img = compress_image(BytesIO(b64decode(img)))
                pd_data[columns[i]] = img
            
            header = get_post_by_ID(**mongoDoc.header.post.to_dict())
            
            if((getSHA(json.dumps({"data":pd_data,"header":header}))!=info.certificateHash)):
                return render(req, "Certificate/HTMX/error.html", context={"error":"Invalid Certificate Credentials"})
            
            report = ReportStructure.get_structure(list(pd_data.keys()))
            
            profile_col = report.profile_img
            
            wid, hei, data = str(pd_data[profile_col]).split(":")

            pd_data[profile_col] = expand_image(width=int(wid),height=int(hei),img_data=data)

            context.update({'data':pd_data,'personal':report.personal_info,'pic':report.profile_img,'sem_dict':report.sem_data,**header})

            return render(req, "Certificate/HTMX/certificate.html", context=context)
        
        except Exception as e:
            context['error'] = DEFAULT_ERROR
        
    return HttpResponse(status=403)

def loadCertificate(req :HttpRequest, certificate: str, cardID:str) -> HttpResponse:
    if(req.method=="GET"):
        context = {"certificate":certificate, "cardID":cardID, 'auth': False}
        if(is_authenticated(req.user)):
            context['auth'] = True
            
        return render(req,"Certificate/index.html",context=context)