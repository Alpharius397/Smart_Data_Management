from django.db import models, transaction
from django.contrib.auth.models import User
from django.conf import settings
import pymongo
from bson.objectid import ObjectId
from django.forms import forms
from typing import NamedTuple

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

    for i in range(1,VERIFY_COUNT+1):
        locals()["verify_%s" % i] = models.ForeignKey(to=User,null=True,blank=True,on_delete=models.SET_NULL,verbose_name="Verify Guy %s" % i,related_name="Verify_%s" % i)
        locals()["verify_%s_status" % i] = models.BooleanField(max_length=12,verbose_name="Verify Guy %s status" % i,null=True,blank=True,default=None,choices=CHOICE)
    
    def clean(self):
        
        verify:list[User] = [self.__getattribute__("verify_%s" % i) for i in range(1,VERIFY_COUNT+1)]
        
        if(any(verify) and (not all(verify))):
            raise forms.ValidationError("Verify Users must be either all empty or all filled")
        
        super().clean()
        
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
        
        update = [{'user':i.username if (i is not None) else None,'status':j} for i,j in zip(verify,verify_status)]
        
        excel = mongo_conn.connect(settings.MONGO_CRED) if mongo_conn else None
        
        if(((not any(verify)) or all(verify)) and (self.mongo_id and self.belongs) and (excel is not None)) and (mongo_session is not None):
            excel.update_one({"_id":ObjectId(self.mongo_id)},{"$set":{"verify":update}},upsert=True,session=mongo_session)
            
        elif(excel):
            raise forms.ValidationError("MongoDB connection failed")
        
        elif(not all(verify)):
            raise forms.ValidationError("Verify Users must be either all empty or all filled")