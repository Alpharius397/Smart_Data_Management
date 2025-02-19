from django.db.models import Model
from django.db.models import CharField, DateTimeField, IntegerField

class LogMessage(Model):
    """ Doesn't Contains traceback as this would be visible to users """
    
    timestamp = DateTimeField(verbose_name="Timestamp of Log",null=False,blank=False)
    mongoID = CharField(max_length=255,verbose_name="MongoID of Record",null=True,blank=True)
    fileName = CharField(max_length=255,verbose_name="Filename of Record",null=True,blank=True)
    index = IntegerField(verbose_name="Index of Record",null=True,blank=True)
    type = IntegerField(verbose_name="Type of Log",null=True,blank=True)
    username = CharField(max_length=255,verbose_name="User of Request Sender",null=True,blank=True)
    userID = IntegerField(verbose_name="User ID of request sender",null=True,blank=True)
    authLevel = CharField(max_length=255,verbose_name="Authentication Level of User",null=False,blank=False)
    action = CharField(max_length=255,verbose_name="Action Performed",null=True,blank=True)
    
    def __str__(self):
        return f"{self.timestamp}-{self.username}-{self.userID}-{self.authLevel}"
    