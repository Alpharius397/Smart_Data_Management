import os
import json
import logging
import traceback
from pathlib import Path
from types import FunctionType, MethodType
from django.utils import timezone
from django.http import HttpRequest
from django.contrib.auth.models import User
from User.models import is_admin, is_manager
from Logs.models import LogMessage

DEFAULT_ERROR = "Something Went Wrong! Please try Again"

class Task:
    EXCEPTION:int = -1
    TASK_UPLOADED:int = 0
    TASK_ASSIGN:int = 1
    TASK_UNASSIGN:int = 2
    TASK_DELETE:int = 3
    TASK_EDIT:int = 4
    DATA_LOCK:int = 5
    DATA_EDIT:int = 6
    DATA_UNLOCK:int = 7
    CARD_READ:int = 8
    FEED_EDIT:int = 9
    

class Auth:
    ADMIN:int = "Admin"
    MANAGER:int = "Manager"
    ANONYMOUS:int = "Anonymous User"


TYPE:dict[int,str] = {0:"Task Uploaded", 1:"Task Assigned", 2:"Task Unassigned", 3:"Task Deleted", 4:"Task Edited", 5:"Data Edited", 6:"Data Locked", 7:"Card Data Downloaded"}

class BaseLogger:
    
    date_time = timezone.now().strftime("%d.%m.%Y")
    
    def __init__(self, dir_path:str) -> None:
        self.__dir_path = dir_path
        self.log = logging.getLogger(self.__class__.__name__)
        MongoLogger.generate_dir(dir_path)
        file_path = os.path.join(dir_path,f'{timezone.now().strftime("%d.%m.%Y")}.log')
        console, self.file = logging.StreamHandler(), logging.FileHandler(file_path,encoding="utf-8")
        formatter = logging.Formatter("[{asctime}]:[{levelname}]:{message}",style="{",datefmt="%d-%m-%Y %H:%M")
        console.setFormatter(formatter)
        self.file.setFormatter(formatter)
        self.log.addHandler(console)        
        self.log.addHandler(self.file)        
        self.log.setLevel(logging.DEBUG)
    
    @staticmethod
    def generate_dir(dir_path:Path) -> None:
        os.makedirs(dir_path,exist_ok=True)
    
    @staticmethod
    def get_error_info(exception:Exception) -> str:
        if(isinstance(exception,Exception)):
            return f"{exception.__class__.__module__}.{exception.__class__.__name__} : {exception}\n{''.join(traceback.format_tb(exception.__traceback__))}"
        else:
            return "Not an exception"
    
    @staticmethod
    def change_decorator(func:FunctionType) -> MethodType:
        
        def wrapper(obj:'BaseLogger', *args, **kwargs,):
            obj.change_time()
            return func(obj, *args, **kwargs)
        
        return wrapper
        
    def change_time(self):
        curr_time = timezone.now().strftime("%d.%m.%Y")
        BaseLogger.generate_dir(self.__dir_path)
        if(self.date_time!=curr_time):
            file_path = os.path.join(self.__dir_path,f'{curr_time}.log')
            
            self.file.setFormatter(logging.FileHandler(file_path,encoding="utf-8"))
        
            self.date_time = curr_time

class MongoLogger(BaseLogger):
    
    @BaseLogger.change_decorator
    def write_error(self, msg:str, where:str = 'MONGODB') -> None:
        self.log.warning(msg=f"[{where}] {msg}\n",exc_info=True)

    @BaseLogger.change_decorator
    def write_info(self, msg:str, where:str = 'MONGODB') -> None:    
        self.log.info(msg=f"[{where}] {msg}\n")

class AppLogger(BaseLogger):

    @BaseLogger.change_decorator
    def write_info(self, msg:'LogStructure') -> None:
        try:
            LogMessage(**msg.get_row()).save()
        except Exception as e:
            temp = msg
            temp.desc.update(type=Task.EXCEPTION,exception=e)
            self.log.error(msg=temp.get_log())
            
        self.log.info(msg=msg.get_log())
    
    @BaseLogger.change_decorator
    def write_error(self, msg:'LogStructure') -> None:
        
        self.log.error(msg=msg.get_log())

class LogStructure:
    """
        Data Structure:
        
            {
                header:{
                    urlPath,
                    timestamps,
                    request:{
                        meta:{
                            GET,
                            POST,
                            FILES,
                            META
                        }
                        userID,
                        userName,
                        auth
                    }
                }
                
                description:{
                    mongoID,
                    fileName,
                    index,
                    type,
                    action,
                }
            }
    """
        
    def __init__(self):
        self.meta = {} # {"GET":None, "POST":None, "FILES":None,"META":None}
        self.request = {} # {"userID":None, "userName":None, "authLevel":None, "META":{}}
        self.header = {} # {"urlPath":None,"timestamp":None,"request":{}}
        self.desc = {} # {"mongoID":None,"fileName":None, "index":None, "type":None,"action":None}
        self.exception = None
        
    def set_request(self, req:HttpRequest):
        url = req.get_full_path()
        user = req.user
        
        if(isinstance(user,User)):
            try:
                userID, userName = user.id, user.username
            except Exception as e:
                pass
        else:
            userID, userName = None, None
        
        timestamp = timezone.now().isoformat()
        
        if(is_admin(user)): authLevel = Auth.ADMIN
        elif(is_manager(user)): authLevel = Auth.MANAGER
        else: authLevel = Auth.ANONYMOUS
        
        meta = ["REMOTE_ADDR","HTTP_HOST","REQUEST_METHOD","REMOTE_ADDR","REMOTE_HOST","HTTP_USER_AGENT"]
        self.meta.update({"GET":req.GET.dict(),"POST":req.POST.dict(),"FILES":{i:{"size":f"{j.size} bytes","file_type":j.content_type,"file_name":j.name} for i,j in req.FILES.items()},"META":{i:req.META.get(i) for i in meta}})
        self.request.update({"userID":userID, "userName":userName, "authLevel":authLevel,"META":self.meta})
        self.header.update({"urlPath":url,"timestamp":timestamp,"request":self.request})
        return self
    
    def get_action(self, type:int, taskID:str = None, index:int = None, column:str = None, manager:User = None, user:User = None, exception: Exception = None, fileName:str = None):

        def dump_detail(what:str, name:str, id:int): return f"{what} {name} (ID: {id})"

        def get_details(user:User) -> dict[str,str]:
            name, id = None, None
            
            try:
                name = user.username
                id = user.id
            except Exception as e:
                pass
            
            return {"name":name, "id":id}

        match(type):
            case Task.TASK_UPLOADED: return f"{dump_detail('Admin',**get_details(user))} uploaded a new {dump_detail('Task','\b',taskID)}"
            case Task.TASK_ASSIGN: return f"{dump_detail('Admin',**get_details(user))} assigned {dump_detail('Manager',**get_details(manager))} to {dump_detail('Task',fileName,taskID)}"
            case Task.TASK_UNASSIGN: return f"{dump_detail('Admin',**get_details(user))} unassigned {dump_detail('Manager',**get_details(manager))} from {dump_detail('Task',fileName,taskID)}"
            case Task.TASK_DELETE: return f"{dump_detail('Admin',**get_details(user))} deleted the {dump_detail('Task',fileName,taskID)}"
            case Task.TASK_EDIT: return f"{dump_detail('Admin',**get_details(user))} re-uploaded the {dump_detail('Task',fileName,taskID)}"
            case Task.DATA_EDIT: return f"{dump_detail('Admin',**get_details(user))} edited the Row {index}, Column {column} of {dump_detail('Task',fileName,taskID)}"
            case Task.DATA_UNLOCK: return f"{dump_detail('Manager',**get_details(user))} unlocked the Row {index} of {dump_detail('Task',fileName,taskID)}"
            case Task.DATA_LOCK: return f"{dump_detail('Manager',**get_details(user))} locked the Row {index} of {dump_detail('Task',fileName,taskID)}"
            case Task.CARD_READ: return f"{dump_detail('Manager',**get_details(user))} downloaded Data regarding Row {index} of {dump_detail('Task',fileName,taskID)}"
            case Task.FEED_EDIT: return f"{dump_detail('Manager',**get_details(user))} provided Feedback on Row {index} of {dump_detail('Task',fileName,taskID)}"
            case _: self.exception = exception
        
        return None
            
    def set_description(self, type:int, taskID:str = None, index:int = None, column:str = None, manager:User = None, user:User = None, exception: Exception = None, fileName:str = None):
        self.desc.update({"mongoID":taskID, "fileName":fileName, "index":index, "type":type,"action":self.get_action(type,taskID,index,column,manager,user,exception,fileName)})
        return self        

    def get_log(self):
        return f"{json.dumps({"header":self.header, "description":self.desc})}\n{BaseLogger.get_error_info(self.exception) if self.exception else ''}"

    def get_row(self):
        return {
            "action":self.desc.get("action",None),
            "mongoID":self.desc.get("mongoID",None),
            "fileName":self.desc.get("fileName",None),
            "index":self.desc.get("index",None),
            "type":self.desc.get("type",None),
            "username":self.request.get("userName",None),
            "userID":self.request.get("userID",None),
            "authLevel":self.request.get("authLevel",None),
            "timestamp":self.header.get("timestamp",None)
        }

