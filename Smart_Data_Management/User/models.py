from django.contrib.auth.models import User,AbstractUser,BaseUserManager
from django.db.models import CharField,CASCADE,OneToOneField,ForeignKey,Model,SET_NULL,EmailField,BooleanField
from University.models import Branch
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import RegexValidator


class Manager(Model):
    user = OneToOneField(to=User,on_delete=CASCADE,related_name='manager')
    belongs = ForeignKey(to=Branch,null=True,blank=False,on_delete=SET_NULL,related_name='manager')
    
    def __str__(self):
        return f"{self.user.username}:{self.belongs}"


class Uploader(Model):
    user = OneToOneField(to=User,on_delete=CASCADE,related_name='uploader')
    belongs = ForeignKey(to=Branch,null=True,blank=False,on_delete=SET_NULL,related_name='uploader')

    def __str__(self):
        return f"{self.user.username}:{self.belongs}"

def is_manager(user:User) -> bool:
    try:
        manager = user.manager
        return True
    except:
        return False

def is_uploader(user:User) -> bool:
    try:
        uploader = user.uploader
        return True
    except:
        return False

"""
class _UserManager(BaseUserManager):
    
    @classmethod
    def create_user(self, username, email, password=None):        
        if not email:
            raise ValueError('User must have an email address')
        if not username:
            raise ValueError('User must have a username')
        
        user = self.model(email=self.normalize_email(email),username=username)

        user.set_password(password)
        user.save()
        return user
    
    @classmethod
    def create_superuser(self, email, username, password):
        user = self.create_user(email=self.normalize_email(email),password=password,username=username)
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user
    
class _User(AbstractUser):
    username = CharField(max_length=225,validators=[UnicodeUsernameValidator],unique=True,null=False,blank=False)
    email = EmailField(max_length=100, unique=True,null=False,blank=False)
    full_name = CharField(max_length=200,null=False,blank=False,validators=[RegexValidator(r'^[a-zA-z]+\Z')])
    is_active = BooleanField(default=True)
    is_admin = BooleanField(default=False)
    is_manager = BooleanField(default=False)
    objects = _UserManager
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'full_name']
"""
    