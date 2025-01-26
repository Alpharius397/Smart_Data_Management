from django.contrib.auth.models import User
from django.db.models import CASCADE,OneToOneField,ForeignKey,Model,SET_NULL
from University.models import Branch

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


class Admin(Model):
    user = OneToOneField(to=User,on_delete=CASCADE,related_name='admin')
    belongs = ForeignKey(to=Branch,null=True,blank=False,on_delete=SET_NULL,related_name='admin')

    def __str__(self):
        return f"{self.user.username}:{self.belongs}"


def is_manager(user:User) -> bool:
    try:
        manager = user.manager
        return True
    except:
        return False

def is_admin(user:User) -> bool:
    try:
        admin = user.admin
        return True
    except:
        return False

def is_uploader(user:User) -> bool:
    try:
        uploader = user.uploader
        return True
    except:
        return False
    
def get_user_by_id(id:int) -> str|None:
    
    user = User.objects.get(id=id)
    return user.username        

def get_post(user: User) -> dict[str,str]:
    uni = None
    insti = None
    branch = None
    
    if(is_manager(user)):
        user:Manager = user.manager
        
    elif(is_uploader(user)):
        user:Uploader = user.uploader
        
    elif(is_admin(user)):
        user:Admin = user.admin
        
    else:
        return {'university':uni,'institute':insti,'branch':branch}
    
    branch = user.belongs
    insti = branch.institute
    uni = insti.university
    
    return {'university':uni.name,'institute':insti.name,'branch':branch.name}

def get_post_id(user:User) -> dict[str,int]:
    uni = None
    insti = None
    branch = None

    if(is_manager(user)):
        user:Manager = user.manager
        
    elif(is_uploader(user)):
        user:Uploader = user.uploader
        
    elif(is_admin(user)):
        user:Admin = user.admin
        
    else:
        return {'university':uni,'institute':insti,'branch':branch}
    
    branch = user.belongs
    insti = branch.institute
    uni = insti.university
    
    return {'university':uni.id,'institute':insti.id,'branch':branch.id}

def is_authenticated(user:User) -> bool:
    
    return bool((user.is_authenticated) and (is_admin(user) or is_manager(user) or is_uploader(user)))


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
    