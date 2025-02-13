from django.contrib.auth.models import User
from django.db.models import OneToOneField,ForeignKey,Model,RESTRICT
from University.models import Branch

class Manager(Model):
    user = OneToOneField(to=User,on_delete=RESTRICT,related_name='manager')
    belongs = ForeignKey(to=Branch,null=True,blank=False,on_delete=RESTRICT,related_name='manager')
    
    def __str__(self):
        return f"{self.user.username}:{self.belongs}"

class Admin(Model):
    user = OneToOneField(to=User,on_delete=RESTRICT,related_name='admin')
    belongs = ForeignKey(to=Branch,null=True,blank=False,on_delete=RESTRICT,related_name='admin')

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

def get_user_by_id(id:int) -> str|None:
    
    try:
        user = User.objects.get(id=id)
        return user.username        
    except:
        return None


def get_user_id(name:int) -> str|None:
    
    try:
        user = User.objects.get(username=name)
        return user.id        
    except:
        return None

def get_post(user: User) -> dict[str,str]:
    uni = None
    insti = None
    branch = None
    
    if(is_manager(user)):
        user:Manager = user.manager

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
    
    elif(is_admin(user)):
        user:Admin = user.admin
        
    else:
        return {'university':uni,'institute':insti,'branch':branch}
    
    branch = user.belongs
    insti = branch.institute
    uni = insti.university
    
    return {'university':uni.id,'institute':insti.id,'branch':branch.id}

def is_authenticated(user:User) -> bool:
    
    return bool((user.is_authenticated) and (is_admin(user) or is_manager(user)))

def get_admin_by_name(username:str) -> list[int]:
    try:
        return list(map(lambda x: x.user.id,Admin.objects.filter(user__username__icontains=username)))
    except Exception as e:
        return []

def get_manager_by_name(username:str) -> list[int]:
    try:
        return list(map(lambda x: x.user.id, Manager.objects.filter(user__username__icontains=username)))
    except Exception as e:
        return []



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
    