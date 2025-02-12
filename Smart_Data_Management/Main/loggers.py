import json
import logging
import os
from django.utils import timezone
from django.http import HttpRequest
# from django.contrib.auth.models import User
# from User.models import is_admin, is_manager
import traceback


# class MongoLogger:
#     def __init__(self, dir_path:str) -> None:
#         self.log = logging.getLogger(__name__)
#         file_path = os.path.join(dir_path,f'{timezone.now().strftime("%d.%m.%Y")}.log')
#         console, file = logging.StreamHandler(), logging.FileHandler(file_path,encoding="utf-8")
#         formatter = logging.Formatter("[{asctime}]:[{levelname}]:{message}",style="{",datefmt="%d-%m-%Y %H:%M")
#         console.setFormatter(formatter)
#         file.setFormatter(formatter)
#         self.log.addHandler(console)        
#         self.log.addHandler(file)        
#         self.log.setLevel(logging.DEBUG)
                
#     def write_error(self, msg:str, where:str = 'MONGODB') -> None:
#         self.log.warning(msg=f"[{where}] {msg}",exc_info=True)

#     def write_info(self, msg:str, where:str = 'MONGODB') -> None:
#         self.log.info(f"[{where}] {msg}")
    
#     @staticmethod
#     def get_error_info(exception:Exception) -> str:
#         if(isinstance(exception,Exception)):
#             return f"{exception.__class__.__module__}.{exception.__class__.__name__} : {exception} \n{''.join(traceback.format_tb(exception.__traceback__))}"
#         else:
#             return "Not an exception"
        

# class AppLogger:
#     def __init__(self, dir_path:str) -> None:
#         self.log = logging.getLogger(__name__)
#         file_path = os.path.join(dir_path,f'{timezone.now().strftime("%d.%m.%Y")}.log')
#         console, file = logging.StreamHandler(), logging.FileHandler(file_path,encoding="utf-8")
#         formatter = logging.Formatter("{message}",style="{",datefmt="%d-%m-%Y %H:%M")
#         console.setFormatter(formatter)
#         file.setFormatter(formatter)
#         self.log.addHandler(console)        
#         self.log.addHandler(file)        
#         self.log.setLevel(logging.DEBUG)
    
#     def write_info(self, msg:str) -> None:
#         self.log.info(f"{msg},")
    
#     @staticmethod
#     def get_error_info(exception:Exception) -> str:
#         if(isinstance(exception,Exception)):
#             return f"{exception.__class__.__module__}.{exception.__class__.__name__} : {exception} \n{''.join(traceback.format_tb(exception.__traceback__))}"
#         else:
#             return "Not an exception"
        

# class LogStructure:
#     """
#         Data Structure:
        
#             {
#                 header:{
#                     urlPath,
#                     timestamps,
#                     request:{
#                         meta:{
#                             GET,
#                             POST,
#                             FILES,
#                             META
#                         }
#                         userID,
#                         userName,
#                         auth
#                     }
#                 }
                
#                 description:{
#                     mongoID,
#                     fileName,
#                     index,
#                     type,
#                     action,
#                 }
#             }
#     """
    
#     TYPE:dict[int,str] = {0:"Task Uploaded", 1:"Task Assigned", 2:"Task Unassigned", 3:"Task Deleted", 4:"Task Edited", 5:"Data Edited", 6:"Data Locked", 7:"Card Data Downloaded"}
#     AUTH:dict[int,str] = {0:"Anonymous User", 1:"Manager", 2:"Admin"}
    
#     def __init__(self):
#         self.meta = {"GET":None, "POST":None, "FILES":None,"META":None}
#         self.request = {"userID":None, "userName":None, "authLevel":None, "META":{}}
#         self.header = {"urlPath":None,"timestamp":None,"request":{}}
#         self.desc = {"mongoID":None,"fileName":None, "index":None, "type":None,"action":None}
    
#     def set_request(self, req:HttpRequest):
#         url = req.get_full_path()
#         user = req.user
        
#         if(isinstance(user,User)):
#             userID, userName = user.id, user.username
#         else:
#             userID, userName = None, None
        
#         timestamp = timezone.now().isoformat()
        
#         if(is_admin(user)): authLevel = 2
#         elif(is_manager(user)): authLevel = 1
#         else: authLevel = 0
        
#         meta = ["REMOTE_ADDR","HTTP_HOST","REQUEST_METHOD","REMOTE_ADDR","REMOTE_HOST","HTTP_USER_AGENT"]
#         self.meta.update({"GET":req.GET.dict(),"POST":req.POST.dict(),"FILES":{i:{"size":f"{j.size} bytes","file_type":j.content_type,"file_name":j.name} for i,j in req.FILES.items()},"META":{i:req.META.get(i) for i in meta}})
#         self.request.update({"userID":userID, "userName":userName, "authLevel":self.AUTH[authLevel],"META":self.meta})
#         self.header.update({"urlPath":url,"timestamp":timestamp,"request":self.request})
#         return self
    
#     def get_action(self, type:int, taskID:str = None, index:int = None, column:str = None, fileName:str = None, manager:str = None, managerID:int = None, user:str = None, userID:int = None, exception: Exception = None):

#         def dump_detail(what:str, name:str, id:int): return f"{what} {name} (ID: {id})"

#         match(type):
#             case 0: return f"{dump_detail('Admin',user,userID)} uploaded a new {dump_detail('Task',fileName,taskID)}"
#             case 1: return f"{dump_detail('Admin',user,userID)} assigned Manager {dump_detail('Manager',manager,managerID)} to {dump_detail('Task',fileName,taskID)}"
#             case 2: return f"{dump_detail('Admin',user,userID)} unassigned {dump_detail('Manager',manager,managerID)} from {dump_detail('Task',fileName,taskID)}"
#             case 3: return f"{dump_detail('Admin',user,userID)} deleted the {dump_detail('Task',fileName,taskID)}"
#             case 4: return f"{dump_detail('Admin',user,userID)} re-uploaded the {dump_detail('Task',fileName,taskID)}"
#             case 5: return f"{dump_detail('Admin',user,userID)} edited the Row {index}, Column {column} of {dump_detail('Task',fileName,taskID)}"
#             case 6: return f"{dump_detail('Manager',user,userID)} locked the Row {index} of {dump_detail('Task',fileName,taskID)}"
#             case 7: return f"{dump_detail('Manager',user,userID)} downloaded Data regarding Row {index} of {dump_detail('Task',fileName,taskID)}"
#             case _: return AppLogger.get_error_info(exception)
            
#     def set_description(self, type:int, taskID:str = None, index:int = None, column:str = None, fileName:str = None, manager:str = None, managerID:int = None, user:str = None, userID:int = None, exception: Exception = None):
#         self.desc.update({"mongoID":taskID,"fileName":fileName, "index":index, "type":type,"action":self.get_action(type,taskID,index,column,fileName,manager,managerID,user,userID,exception)})
#         return self        

#     def get_log(self):
#         return {"header":self.header, "description":self.desc}


lasd = '{{"0":"2"},{"2":"1"}}'
print(json.loads(lasd))