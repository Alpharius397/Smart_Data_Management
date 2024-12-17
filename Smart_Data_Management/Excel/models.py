from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
import pymongo
from bson.objectid import ObjectId
from django.forms import forms

class VerificationTable(models.Model):
    mongo_id = models.CharField(max_length=24,null=False,verbose_name="Mongo Object ID")
    belongs = models.ForeignKey(to=User,null=False,verbose_name="Belongs to ",on_delete=models.CASCADE,related_name="belongs")
    verify_1 = models.ForeignKey(to=User,null=True,blank=True,on_delete=models.SET_NULL,verbose_name="Verify Guy 1",related_name="Verify_1")
    verify_1_done = models.BooleanField(verbose_name="Verify Guy 1 done",null=False,default=False)
    verify_2 = models.ForeignKey(to=User,null=True,blank=True,on_delete=models.SET_NULL,verbose_name="Verify Guy 2",related_name="Verify_2")
    verify_2_done = models.BooleanField(verbose_name="Verify Guy 2 done",null=False,default=False)
    verify_3 = models.ForeignKey(to=User,null=True,blank=True,on_delete=models.SET_NULL,verbose_name="Verify Guy 3",related_name="Verify_3")
    verify_3_done = models.BooleanField(verbose_name="Verify Guy 3 done",null=False,default=False)

    
    def clean(self):
        connect = pymongo.MongoClient(settings.MONGO_URL)
    
        excel = connect["smart"]["excel"]
        
        
        verify = [self.__getattribute__("verify_%s" % i) for i in range(1,4)]
        
        if(((not any(verify)) or all(verify)) and (self.mongo_id and self.belongs)):
            update = [{'user':self.__getattribute__("verify_%s" % i).username,'verify':False} for i in range(1,4) if self.__getattribute__("verify_%s" % i) is not None]
            excel.update_one({"_id":ObjectId(self.mongo_id)},{"$set":{"verify":update}})
        else:
            raise forms.ValidationError("Verify Users must be either all empty or all filled")
        
        super().clean()
        
    def save(self):
        self.clean()
        return super().save()
        
            
        