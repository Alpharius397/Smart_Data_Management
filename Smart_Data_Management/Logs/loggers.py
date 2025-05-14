from functools import wraps
import os
import json
import logging
import traceback
from pathlib import Path
from typing import Callable, ParamSpec
from django.utils import timezone #type: ignore
from django.http import HttpRequest #type: ignore
from django.contrib.auth.models import User #type: ignore
from User.models import is_admin, is_manager #type: ignore
from Logs.models import LogMessage 
from django.conf import settings #type: ignore
from constants.constants import *

P = ParamSpec("P")

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
    CARD_ISSUE:int = 8
    FEED_EDIT:int = 9
    CARD_CANCEL:int = 10
    UNAUTH_REQ:int = 11
    CARD_DATA_FETCH:int = 12
    INVALID_TOKEN:int = 13
    INVALID_ID: int = 14
    WEBSOCKET_FAILED: int = 15

class Auth:
    ADMIN:str = "Admin"
    MANAGER:str = "Manager"
    ANONYMOUS:str = "Anonymous User"

class BaseLogger:
    
    def __init__(self, dir_path: Path) -> None:
        self.date_time = timezone.now().strftime("%d.%m.%Y")
        self.__dir_path = dir_path
        self.log = logging.getLogger(self.__class__.__name__)
        MongoLogger.generate_dir(dir_path)
        file_path = os.path.join(dir_path,f'{timezone.now().strftime("%d.%m.%Y")}.log')
        console, file = logging.StreamHandler(), logging.FileHandler(file_path,encoding="utf-8")
        formatter = logging.Formatter("[{asctime}]:[{levelname}]:{message}",style="{",datefmt="%d-%m-%Y %H:%M")
        console.setFormatter(formatter)
        file.setFormatter(formatter)
        self.log.addHandler(console)        
        self.log.addHandler(file)        
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
    def change_decorator(func: Callable[P, None]) -> Callable[P, None]:

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> None:
            if args:
                if isinstance(args[0], BaseLogger):
                    args[0].change_time()
                    
            return func(*args, **kwargs)
        
        return wrapper
        
    def change_time(self):
        curr_time = timezone.now().strftime("%d.%m.%Y")
        BaseLogger.generate_dir(self.__dir_path)

        if(self.date_time!=curr_time):
            file_path = os.path.join(self.__dir_path, f'{curr_time}.log')

            for handler in self.log.handlers[:]:
                if isinstance(handler, logging.FileHandler):
                    self.log.removeHandler(handler)

            file_handler = logging.FileHandler(file_path, encoding="utf-8")
            formatter = logging.Formatter("[{asctime}]:[{levelname}]:{message}", style="{", datefmt="%d-%m-%Y %H:%M")
            file_handler.setFormatter(formatter)
            self.log.addHandler(file_handler)

            self.date_time = curr_time


class MongoLogger(BaseLogger):
    
    @BaseLogger.change_decorator
    def write_error(self, msg:str, where:str = 'MONGODB') -> None:
        self.log.warning(msg=f"[{where}] {msg}\n",exc_info=True)

    @BaseLogger.change_decorator
    def write_info(self, msg:str, where:str = 'MONGODB') -> None:
        self.log.info(msg=f"[{where}] {msg}\n")

class RedisLogger(BaseLogger):
    
    @BaseLogger.change_decorator
    def write_error(self, msg:str, where:str = 'REDIS') -> None:
        self.log.warning(msg=f"[{where}] {msg}\n",exc_info=True)

    @BaseLogger.change_decorator
    def write_info(self, msg:str, where:str = 'REDIS') -> None:
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

APP_LOG, MONGO_LOG, REDIS_LOG = AppLogger(settings.APP_LOG), MongoLogger(settings.DATA_LOG), RedisLogger(settings.DATA_LOG)
""" Shared Log Instance """


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
    
    def get_action(self, type:int, taskID:str|None = None, index:int|None = None, column:str|None = None, manager:User = None, user:User = None, exception: Exception|None = None, fileName:str|None = None):

        def dump_detail(what:str, name:str|None, iD:int|str|None): return f"{what} {name} (ID: {iD})"

        def get_details(user:User) -> dict[str, str | int | None]:
            
            name:str | None = None
            iD: int | None = None
            
            try:
                name = user.username
                iD = user.id
            except Exception as e:
                pass
            
            return {"name":name, "iD":iD}

        match(type):
            case Task.TASK_UPLOADED: return f"{dump_detail('Admin',**get_details(user))} uploaded a new {dump_detail('Task','\b',taskID)}" #type: ignore
            case Task.TASK_ASSIGN: return f"{dump_detail('Admin',**get_details(user))} assigned {dump_detail('Manager',**get_details(manager))} to {dump_detail('Task',fileName,taskID)}" #type: ignore
            case Task.TASK_UNASSIGN: return f"{dump_detail('Admin',**get_details(user))} unassigned {dump_detail('Manager',**get_details(manager))} from {dump_detail('Task',fileName,taskID)}" #type: ignore
            case Task.TASK_DELETE: return f"{dump_detail('Admin',**get_details(user))} deleted the {dump_detail('Task',fileName,taskID)}" #type: ignore
            case Task.TASK_EDIT: return f"{dump_detail('Admin',**get_details(user))} re-uploaded the {dump_detail('Task',fileName,taskID)}" #type: ignore
            case Task.DATA_EDIT: return f"{dump_detail('Admin',**get_details(user))} edited the Row {index}, Column {column} of {dump_detail('Task',fileName,taskID)}" #type: ignore
            case Task.DATA_UNLOCK: return f"{dump_detail('Manager',**get_details(user))} unlocked the Row {index} of {dump_detail('Task',fileName,taskID)}" #type: ignore
            case Task.DATA_LOCK: return f"{dump_detail('Manager',**get_details(user))} locked the Row {index} of {dump_detail('Task',fileName,taskID)}" #type: ignore
            case Task.CARD_ISSUE: return f"{dump_detail('Manager',**get_details(user))} has issued card with data regarding Row {index} of {dump_detail('Task',fileName,taskID)}" #type: ignore
            case Task.FEED_EDIT: return f"{dump_detail('Manager',**get_details(user))} provided Feedback on Row {index} of {dump_detail('Task',fileName,taskID)}" #type: ignore
            case Task.CARD_CANCEL: return f"{dump_detail('Manager',**get_details(user))} has cancelled card with data regarding Row {index} of {dump_detail('Task',fileName,taskID)}" #type: ignore
            case Task.UNAUTH_REQ: return f"Received unauthorized request for Card Issue"
            case Task.CARD_DATA_FETCH: return f"Authenticated Card Data Fetch"
            case Task.INVALID_TOKEN: return f"Token is either expired or completed!"
            case Task.INVALID_ID: return f"Card ID was not found!"
            case Task.WEBSOCKET_FAILED: return f"Web Socket Failed"
            case _: self.exception = exception
        
        return None
            
    def set_description(self, type:int, taskID:str|None = None, index:int|None = None, column:str|None = None, manager:User = None, user:User = None, exception: Exception|None = None, fileName:str|None = None):
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

