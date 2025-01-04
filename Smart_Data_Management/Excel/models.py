from django.db import models
from django.conf import settings
import pymongo
from bson.objectid import ObjectId
from django.forms import forms
from typing import NamedTuple
import pymongo.client_session
import pymongo.collection
from User.models import Uploader, Manager
from typing import Any

class MongoDB(NamedTuple):
    database:str
    collection:str
    
class Choice(NamedTuple):
    DB_VALUE:str
    FORM_VALUE:str

CHOICE:list[Choice] = [(True,'Verified'),(False,'Rejected'),(None,'Unchecked')]
VERIFY_COUNT:int = 1

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

class MongoTemplate:
        
    def __init__(self, file_name:str ,data:dict[str,Any], belongs:str, image_idx:list[int] = []) -> None:
        
        self.excel = {'data':data,'name':file_name,'image':image_idx}
        self.belongs = belongs
        self.verify = []

    def get_json(self):
        
        to_get = ['excel','belongs','verify']
        
        return {i:self.__getattribute__(i) for i in to_get}


class VerificationTable(models.Model):
    mongo_id = models.CharField(max_length=24,null=False,verbose_name="Object ID",primary_key=True)
    belongs = models.ForeignKey(to=Uploader,null=False,verbose_name="Belongs to",on_delete=models.CASCADE,related_name="belong")
    assigned = models.ForeignKey(to=Manager,null=True,verbose_name="Assigned to",on_delete=models.SET_NULL,related_name="assign")
    assigned_status = models.BooleanField(max_length=12,verbose_name="Assigned status",null=True,blank=True,default=None,choices=CHOICE)
    assigned_feedback = models.CharField(max_length=255,verbose_name="Assigned Feedback",null=True,blank=True,default='')
    
    class Meta:
        verbose_name = "Verification Record"
        verbose_name_plural = "Verification Records"
    
    def clean_assigned(self):
        belong = self.belongs.user.username
        assigned = self.assigned.user.username
        
        if(belong==assigned):
            raise forms.ValidationError("Assigned user cannot also be the uploader")
        
        return self.assigned
                
    def save(self):
        
        super().clean()
        
        if(self.mongo_insert()):
            super().save()
        else:
            super().delete()

    
    def delete(self, **kwargs):
        connection = MongoConnection(settings.MONGO_URL)
        
        excel = connection.connect(settings.MONGO_CRED)
        
        if(excel is None):
            raise forms.ValidationError("MongoDB connection failed")
            
        excel.delete_one({"_id":ObjectId(self.mongo_id)})
        
        return super().delete(**kwargs)   
    
    def is_owner(self, user):
        return self.belongs.user==user   
    
    def is_assigned(self, user):
        return self.assigned.user==user
        
    def mongo_insert(self, mongo_conn:MongoConnection = None):
            
        if(self.assigned is None):
            self.assigned_feedback = ''
            self.assigned_status = None
            
        verify:list[Manager] = [self.assigned]
        verify_status:list[bool|None] = [self.assigned_status]
        verify_feed:list[str|None] = [self.assigned_feedback]
        
        update = [{'user':i.user.username if (i is not None) else None,'status':j,'feedback':k} for i,j,k in zip(verify,verify_status,verify_feed)]
        
        mongo_conn = MongoConnection(settings.MONGO_URL)
        excel = mongo_conn.connect(settings.MONGO_CRED)
        
        updated = False
        
        if(excel is not None):
            record = excel.update_one({"_id":ObjectId(self.mongo_id)},{"$set":{"verify":update}})
            updated = bool(record.matched_count==1)
            
        else:
            raise forms.ValidationError("MongoDB connection failed")
        
        return updated
        
    def __str__(self):
        return f"{self.belongs.user} - {self.mongo_id}"