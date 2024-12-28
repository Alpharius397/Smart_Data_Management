from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
import pymongo
from bson.objectid import ObjectId
from django.forms import forms
from typing import NamedTuple
import pymongo.client_session
import pymongo.collection
from Main.models import Uploader, Manager

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
    belongs = models.ForeignKey(to=Uploader,null=False,verbose_name="Belongs to ",on_delete=models.CASCADE,related_name="belongs")

    for i in range(VERIFY_COUNT):
        locals()["verify_%s" % (i+1)] = models.ForeignKey(to=Manager,null=True,blank=True,on_delete=models.SET_NULL,verbose_name="Verify Guy %s" % (i+1),related_name="Verify_%s" % (i+1))
        locals()["verify_%s_status" % (i+1)] = models.BooleanField(max_length=12,verbose_name="Verify Guy %s status" % (i+1),null=True,blank=True,default=None,choices=CHOICE)
        locals()["verify_%s_feedback" % (i+1)] = models.CharField(max_length=255,verbose_name="Verify Guy %s Feedback" % (i+1),null=True,blank=True,default='')
    
    def get_verify(self):
        return [self.__getattribute__("verify_%s" % (i+1)) for i in range(VERIFY_COUNT)]
    
    def get_verify_status(self):
        return [self.__getattribute__("verify_%s_status" % (i+1)) for i in range(VERIFY_COUNT)]
    
    def get_feedback(self):
        return [self.__getattribute__("verify_%s_feedback" % (i+1)) for i in range(VERIFY_COUNT)]
        
    
    def clean(self):
        
        verify:list[User] = self.get_verify()
        
        if(any(verify) and (not all(verify))):
            raise forms.ValidationError("Verify Users must be either all empty or all filled")
        
        if((all(verify)) and len(set(verify))<len(verify)):
            raise forms.ValidationError("Different user must be assigned to each task")
        
        super().clean()
        
    def clean_belongs(self):
        verify:list[User] = self.get_verify()
        
        if(self.belongs in verify):
            raise forms.ValidationError("Uploader cannot also be in verification team")
                
    def save(self):
        
        connection = MongoConnection(settings.MONGO_URL)
        super().clean()
        self.mongo_insert(connection)
        super().save()

    
    def delete(self, **kwargs):
        connection = MongoConnection(settings.MONGO_URL)
        
        excel = connection.connect(settings.MONGO_CRED)
        
        if(excel is None):
            raise forms.ValidationError("MongoDB connection failed")
            
        excel.delete_one({"_id":ObjectId(self.mongo_id)})
        
        return super().delete(**kwargs)   
    
    def get(self, attrs, default = None):
        try:
            val = self.__getattribute__(attrs) 
            return val
        except Exception as e:
            return default
        
    def get_user(self, username):
        
        verify = self.get_verify()
        
        return verify.index(username) + 1 if(username in verify) else None
    
    def is_owner(self, username):
        return self.belongs.user==username   
    
    def set(self, attr, value):
        self.__setattr__(attr,value)
        
    def set_verify(self, idx:int, status:bool, feedback:str):
        self.set("verify_%s_status" % (idx),status)
        self.set("verify_%s_feedback" % (idx),feedback)
        
        
    def mongo_insert(self, mongo_conn:MongoConnection = None):
            
        verify:list[User] = self.get_verify()
        
        for i in range(VERIFY_COUNT):
            if(verify[i] is None):
                self.set("verify_%s_status" % (i+1),None)
                self.set("verify_%s_feedback" % (i+1),'')
        
        verify_status:list[bool] = self.get_verify_status()
        verify_feed:list[str] = self.get_feedback()

        update = [{'user':i.user.username if (i is not None) else None,'status':j,'feedback':k} for i,j,k in zip(verify,verify_status,verify_feed)]
        
        excel = mongo_conn.connect(settings.MONGO_CRED) if mongo_conn else None
        
        if((excel is not None)):
            excel.update_one({"_id":ObjectId(self.mongo_id)},{"$set":{"verify":update}},upsert=True)
            
        elif((excel is None) or (mongo_conn is None)):
            raise forms.ValidationError("MongoDB connection failed")
        
        else:
            raise forms.ValidationError("Something went wrong")
        
        
    def __str__(self):
        return f"{self.belongs.user} - {self.mongo_id}"