from django.db import models

# Create your models here.
class User(models.Model):
    username = models.CharField(primary_key=True,max_length=100,null=False,blank=False)
    password = models.CharField(max_length=255,null=False,blank=False)
    email = models.EmailField(unique=True,null=False,blank=False)
    
    def __str__(self):
        return "%(user)s %(email)s" % {'user':self.username, 'email':self.email}
    
    
class ShiftTiming(models.Model):
    in_time = models.TimeField(null=False,blank=False)
    out_time = models.TimeField(null=False,blank=False)
    sign = models.CharField(max_length=10,null=False,blank=False)
    
    def __str__(self):
        return "%(sym)s => [%(in)s - %(out)s]" % {'sym':self.sign,'in':self.in_time,'out':self.out_time}