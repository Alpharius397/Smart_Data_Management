from django.db import models, transaction
from django.contrib.auth.models import User
from django.conf import settings
import pymongo
from bson.objectid import ObjectId
from django.forms import forms
from typing import NamedTuple
import re
import pymongo.client_session
import pymongo.collection


class MongoDB(NamedTuple):
    database:str
    collection:str
    
class Choice(NamedTuple):
    DB_VALUE:str
    FORM_VALUE:str

CHOICE:list[Choice] = [(True,'Verified'),(False,'Rejected'),(None,'Unchecked')]
VERIFY_COUNT:int = 3


def get_error_info(exception:Exception) -> str:
    if(isinstance(exception,Exception)):
        return f"{exception.__class__.__module__}.{exception.__class__.__name__} : {exception}"
    
    return "Not an Exception"
    
class MongoConnection:
    connection:pymongo.MongoClient = None
    
    def __init__(self, connect_url:str) -> None:
        self.connection = pymongo.MongoClient(connect_url)
    
    def connect(self, info:MongoDB) -> pymongo.collection.Collection | None:

        try:
            self.connection.server_info()
            return self.connection.get_database(info.database).get_collection(info.collection)
        except Exception as e:            
            print(get_error_info(e))
            
        return None

class VerificationTable(models.Model):
    mongo_id = models.CharField(max_length=24,null=False,verbose_name="Mongo Object ID",primary_key=True)
    belongs = models.ForeignKey(to=User,null=False,verbose_name="Belongs to ",on_delete=models.CASCADE,related_name="belongs")
    no_of_rows = models.IntegerField(verbose_name="No of Rows in data",null=False,default=0)

    for i in range(1,VERIFY_COUNT+1):
        locals()["verify_%s" % i] = models.ForeignKey(to=User,null=True,blank=True,on_delete=models.SET_NULL,verbose_name="Verify Guy %s" % i,related_name="Verify_%s" % i)
        locals()["verify_%s_status" % i] = models.BooleanField(max_length=12,verbose_name="Verify Guy %s status" % i,null=True,blank=True,default=None,choices=CHOICE)
        locals()["verify_assign_%s" % i] = models.CharField(max_length=255,verbose_name="Verify Assignment %s" % i,null=True,blank=True)
    
    def clean(self):
        
        verify:list[User] = [self.__getattribute__("verify_%s" % i) for i in range(1,VERIFY_COUNT+1)]
        verify_assign:list[str] = [self.__getattribute__("verify_assign_%s" % (i+1)) for i in range(VERIFY_COUNT)]
        count:int = 0
        
        SINGLE_RE = r'^(\d+)$'
        RANGE_RE = r'^(\d+)\-(\d+)$'
        
        for idx,i in enumerate(verify_assign):
            
            if(verify[idx] is None): continue
            
            
            if(i is None):
                raise forms.ValidationError("Must assign rows to user")
            
            comma = i.split(',')
            
            for j in comma:
                
                _single = re.findall(SINGLE_RE,j)
                _range = re.findall(RANGE_RE,j)
                
                if(_single):
                    a = int(_single[0])
                    
                    if(a<=0 or a>self.no_of_rows): 
                        raise forms.ValidationError("Numbering out of range")
                    
                    count += 1
                
                elif(_range):
                    b,c = map(int,_range[0])
                    
                    if((b<0 or b>self.no_of_rows) or (c<0 or c>self.no_of_rows)):
                        raise forms.ValidationError("Numbering out of range")
                    elif(b>c):
                        raise forms.ValidationError("Numbering should be in order.Eg: 1-3, not 3-1")
                    
                    count += c - b + 1
                
                else:
                    raise forms.ValidationError("Numbering range should be of form: 1-100 or 4 (separated by comma)")
                
                
        if(all(verify) and count!=self.no_of_rows):
            raise forms.ValidationError("All rows must be assigned")
        
        if(any(verify) and (not all(verify))):
            raise forms.ValidationError("Verify Users must be either all empty or all filled")
        
        if(len(set(verify))<len(verify)):
            raise forms.ValidationError("Different user must be assigned to each task")
        
        super().clean()
                
        
    def clean_belongs(self):
        verify:list[User] = [self.__getattribute__("verify_%s" % i) for i in range(1,VERIFY_COUNT+1)]
        
        if(self.belongs in verify):
            raise forms.ValidationError("Uploader cannot also be in verification team")
                
    def save(self):
        
        connection = MongoConnection(settings.MONGO_URL)
        
        with connection.connection.start_session() as conn:
            self.mongo_insert(connection,conn)
            super().clean()
            super().save()
    
    
    def delete(self, **kwargs):
        connection = MongoConnection(settings.MONGO_URL)
        
        excel = connection.connect(settings.MONGO_CRED)
        
        if(excel is None):
            raise forms.ValidationError("MongoDB connection failed")
            
        
        with connection.connection.start_session() as conn:
            excel.delete_one({"_id":ObjectId(self.mongo_id)},session=conn)
            
            return super().delete(**kwargs)            
        
        
    def mongo_insert(self, mongo_conn:MongoConnection = None ,mongo_session:pymongo.client_session.ClientSession = None):
            
        verify:list[User] = [self.__getattribute__("verify_%s" % (i+1)) for i in range(VERIFY_COUNT)]
        
        for i in range(VERIFY_COUNT):
            if(verify[i] is None):
                self.__setattr__("verify_%s_status" % (i+1),None)
        
        verify_status:list[bool] = [self.__getattribute__("verify_%s_status" % (i+1)) for i in range(VERIFY_COUNT)]
        verify_assign:list[str] = [self.__getattribute__("verify_assign_%s" % (i+1)) for i in range(VERIFY_COUNT)]
        
        update = [{'user':i.username if (i is not None) else None,'status':j,'assign':k} for i,j,k in zip(verify,verify_status,verify_assign)]
        
        excel = mongo_conn.connect(settings.MONGO_CRED) if mongo_conn else None
        
        if(((not any(verify)) or all(verify)) and (self.mongo_id and self.belongs) and (excel is not None)) and (mongo_session is not None):
            asd = excel.update_one({"_id":ObjectId(self.mongo_id)},{"$set":{"verify":update}},upsert=True,session=mongo_session)
        elif(excel):
            raise forms.ValidationError("MongoDB connection failed")
        
        elif(not all(verify)):
            raise forms.ValidationError("Verify Users must be either all empty or all filled")
        else:
            raise forms.ValidationError("Something went wrong")
        
        
    def __str__(self):
        return f"{self.belongs} - {self.mongo_id}"