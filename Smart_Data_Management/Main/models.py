from django.db import models
from django.contrib.auth.models import User



class Manager(models.Model):
    user = models.OneToOneField(to=User,on_delete=models.CASCADE,related_name='manager')
    
    def __str__(self):
        return self.user.username

class Uploader(models.Model):
    user = models.OneToOneField(to=User,on_delete=models.CASCADE,related_name='uploader')

    def __str__(self):
        return self.user.username