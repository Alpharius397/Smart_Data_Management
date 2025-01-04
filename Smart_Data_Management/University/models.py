from django.contrib.auth.models import User
from django.db.models import CharField,CASCADE,OneToOneField,ForeignKey,Model,SET_NULL


class University(Model):
    name = CharField(max_length=200,null=False,blank=False,verbose_name='University Name')
    
    class Meta:
        verbose_name = "University"
        verbose_name_plural = "Universities"
        
    def __str__(self):
        return self.name

class Institute(Model):
    name = CharField(max_length=200,null=False,blank=False,verbose_name='Institute Name')
    university = ForeignKey(to=University,null=False,blank=False,related_name='insti',on_delete=CASCADE)
    location = CharField(max_length=200,null=False,blank=False,verbose_name='Location')
    
    class Meta:
        verbose_name = "Institute"
        verbose_name_plural = "Institutes"
    
    def __str__(self):
        return f"{self.university}:{self.name}"
    
class Branch(Model):
    name = CharField(max_length=200,null=False,blank=False,verbose_name='Branch Name')
    institute = ForeignKey(to=Institute,null=False,on_delete=CASCADE,related_name='branch')

    class Meta:
        verbose_name = "Branch"
        verbose_name_plural = "Branches"

    def __str__(self):
        return f"{self.institute}:{self.name}"

