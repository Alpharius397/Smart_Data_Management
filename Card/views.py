from typing import Any, NamedTuple, TypedDict, Literal
from django.http import HttpRequest, JsonResponse  # type: ignore
from Card.errors import CardIdMissing
from Report.errors import DataNotLocked
from Report.views import getReport
from University.models import Subject
from Task.models import DataTable, TaskTable
from Main.settings import settingsInterface as settings
from User.models import (
    get_post_id,
    get_user,
    get_post,
    is_authenticated, 
    is_manager,
    User
)
from tools.encrypt import decrypt_key, decrypt_text, encrypt_data, decrypt_data, encrypt_text
from tools.errors import TokenExpired
from tools.get_image import expand_image
from tools.url_auth import (
    is_auth_post,
    api_key_required,
    auth_needed,
    task_permission_check,
    token_check,
)
from Logs.loggers import APP_LOG, LogStructure, LogType
from tools.utils import get_2_value, setSwalAlert
from django.views.decorators.csrf import csrf_exempt  # type: ignore
from Card.models import Card
from django.db import transaction # type: ignore
from django.utils import timezone # type: ignore
from constants import DEFAULT_ERROR
from Main.models import AsyncRedisConnection, ReadToken, RedisConnection, RedisDataBase, WriteToken
import json
from channels.generic.websocket import AsyncWebsocketConsumer, DenyConnection # type: ignore
from tools.token import hash_token
from asgiref.sync import sync_to_async, async_to_sync
from django.template.loader import render_to_string # type: ignore
from channels.layers import get_channel_layer # type: ignore

############ TYPES ############

class FetchJson(TypedDict):
    data: str
    
class ReadJson(TypedDict):
    message: str
    status: Literal['true', 'false', 'none']
    card: str
    data: str

class ConfirmJson(TypedDict):
    message: str
    status: Literal['true', 'false', 'none']
    card: str
    
class SubjectMeta(TypedDict):
    sem: int
    marks: int

class SemMeta(NamedTuple):
    marks: int
    total: int
    
class EncryptData(TypedDict):
    university: str
    institute: str
    branch: str
    images: dict[str, str]
    personal: dict[str, str]
    sem_data: dict[int, dict[str, tuple[int, int]]]

@csrf_exempt
@api_key_required # type: ignore
@token_check(RedisDataBase.CARD_WRITE_TOKEN, close_after=False)
@auth_needed(manager_only=True)
@task_permission_check
def fetch_data(req: HttpRequest, id: int, idx: str, schema: int, token: str):
    
    user = get_user(req)
    task: TaskTable = req.__getattribute__("task")
    context:dict[str, Any] = {}
    
    if(is_auth_post(req)):
        try:
            post = get_post_id(user)
            
            feed = DataTable.get_complete_feed(task, id, idx)
            
            if feed.locked is False:
                raise DataNotLocked()
            
            sem_dict = Subject.getSubjects(schema, post["branch"]) # type: ignore  
                
            post = get_post_id(user)
            sem_dict = Subject.getSubjects(schema, post["branch"]) # type: ignore
            
            report_data = getReport(sem_dict, task, id, idx, True)
            context.update(get_post(user))
            context.update(report_data)
            
            with RedisConnection(RedisDataBase.CARD_WRITE_TOKEN) as redis:
                writeToken = WriteToken(**redis.getDict(token))
                encrypted = encrypt_data(decrypt_key(writeToken["key"]).encode(), context)
                
                APP_LOG.write_info(LogStructure().set_request(req, LogType.CARD_DATA_FETCH, id, rowID=idx).set_meta(req))
                
                return JsonResponse(data=FetchJson(data=encrypted), safe=True, status=200)
        
        except DataNotLocked as f:
            return JsonResponse(data=FetchJson(data=f.get_error()), safe=True, status=401)
        
        except Exception as e:
            APP_LOG.write_info(LogStructure().set_request(req, LogType.EXCEPTION, id, rowID=idx).set_meta(req).set_error(e))
            return JsonResponse(data=FetchJson(data=DEFAULT_ERROR), safe=True, status=500)

@csrf_exempt
@api_key_required # type: ignore
@token_check(RedisDataBase.CARD_WRITE_TOKEN)
@auth_needed(manager_only=True)
@task_permission_check
def confirm_view(req: HttpRequest, id: int, idx: str, schema: int, token: str):
    user = get_user(req)
    task: TaskTable = req.__getattribute__("task")
    context: dict = {}
    if is_auth_post(req):
        
        try:
            with transaction.atomic():
                data = ConfirmJson(**req.POST.dict()) # type: ignore
                post = get_post_id(user)
                sem_dict = Subject.getSubjects(schema, post["branch"]) # type: ignore
                
                issued = data["status"]
                cardID = data['card']
                
                if(not cardID):
                    raise CardIdMissing()
                
                context.update({**get_post(user), **getReport(sem_dict, task, id, idx)})
                
                DataTable.set_complete_feed(task, id, idx, issued=get_2_value(issued)) # type: ignore
                
                card, _ = Card.objects.get_or_create(cardID=cardID)
                
                with RedisConnection(RedisDataBase.CARD_WRITE_TOKEN) as redis:
                    writeToken = WriteToken(**redis.getDict(token))
                    
                    card.data = context # type: ignore
                    card.last_write = timezone.now()
                    card.done_by = user
                    card.decryption_key = writeToken["key"]
                    
                card.save()
                cardWriteWebSocket(token, data)
                
                APP_LOG.write_info(LogStructure().set_request(req, LogType.CARD_DATA_FETCH, id, rowID=idx).set_meta(req))
                
                return JsonResponse(data={"status": "Feedback updated successfully"}, status=200)
            
        except CardIdMissing as f:
            data = ConfirmJson(message=f.get_error(), status='false', card="")
            cardWriteWebSocket(token, data)
            return JsonResponse(data={"status": "Feedback updation failed"}, status=401)
            
        except Exception as e:
            APP_LOG.write_info(LogStructure().set_request(req, LogType.EXCEPTION, id, rowID=idx).set_meta(req).set_error(e))
            data = ConfirmJson(message=DEFAULT_ERROR, status='none', card="")
            cardWriteWebSocket(token, data)
            return JsonResponse(data={"status": "Feedback updation failed"}, status=500)


@csrf_exempt
@api_key_required # type: ignore
@token_check(RedisDataBase.CARD_READ_TOKEN)
@auth_needed(manager_only=True)
def read_view(req: HttpRequest, token: str):
    if is_auth_post(req):
        
        try:
            data = ReadJson(**req.POST.dict()) # type: ignore
            
            if(not data["card"]):
                raise CardIdMissing()
            
            cardReadWebSocket(token, data)
            return JsonResponse(data={"status": "Card Data received successfully"}, status=200)
        
        except CardIdMissing as f:
            data = ReadJson(message=f.get_error(), status='false', card="", data="")
            cardReadWebSocket(token, data)
            return JsonResponse(data={"status": "Card ID missing"}, status=401)
            
        except Exception as e:
            APP_LOG.write_info(LogStructure().set_request(req, LogType.EXCEPTION).set_meta(req).set_error(e))
            data = ReadJson(message=DEFAULT_ERROR, status='none', card="", data="")
            cardReadWebSocket(token, data)
            return JsonResponse(data={"status": "Card Data received failed"}, status=500)

        
def cardWriteWebSocket(token: str, data: ConfirmJson):
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(token, {"type": "card.write", **data}) # type: ignore
    except Exception as e:
        pass
    
class CardWriteExeConsumer(AsyncWebsocketConsumer):
    
    user: User
    taskID: int
    idx: int
    token: str

    async def auth_user(self) -> bool:
        try:
            user: User = self.user
            managerFlag = await sync_to_async(is_manager)(user)
            authFlag = await sync_to_async(is_authenticated)(user)
            
            return bool(managerFlag and authFlag)
        except Exception as e:
            return False
    
    async def auth_token(self) -> bool:
        try:
            async with AsyncRedisConnection(RedisDataBase.CARD_WRITE_TOKEN) as redis:
                data: WriteToken | ReadToken = await redis.getDict(self.token) # type: ignore
                
                processing = data.get("processing", None)
                ID = data.get("ID", -1)
                
                if (not isinstance(processing, bool)) or (isinstance(processing, bool) and (processing is not True)):
                    raise TokenExpired()
                
                user = await User.objects.aget(id=ID)
                
                return (self.user.id == user.id)
            
        except Exception as e:
            return False
    
    async def connect(self) -> None:
        
        try:
            self.taskID = self.scope["url_route"]["kwargs"]["id"]
            self.idx = self.scope["url_route"]["kwargs"]["idx"]
            self.token = self.scope["url_route"]["kwargs"]["token"]
            self.user = self.scope["user"]
            
            self.room_group_name = self.token
            
            tokenFlags = await self.auth_token()
            userFlags = await self.auth_user()
            
            if(not (tokenFlags and userFlags)):
                raise DenyConnection("Unauthenticated User")
            
            await self.channel_layer.group_add(self.room_group_name, self.channel_name) # type: ignore

            await self.accept()
        
        except DenyConnection as f:
            raise f
        
        except Exception as e:
            raise DenyConnection("Invalid URL found!")

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name) # type: ignore

    # Receive message from WebSocket
    async def receive(self, text_data: str): # type: ignore
        APP_LOG.write_error(LogStructure().set_error(Exception("No Entry Here")))
    
    async def card_write(self, event: ConfirmJson):
        status = event.get("status",'none')
        message = event.get("message", DEFAULT_ERROR)
        context = setSwalAlert(title="Card Write")
        
        match(status):
            case "true":
                setSwalAlert(context, message, "success")
            case "false":
                setSwalAlert(context, message, "warning")
            case _:
                setSwalAlert(context, message)
                
        await self.send(text_data=render_to_string('Report/HTMX/write/end.html',context=context), close=True)

def cardReadWebSocket(token: str, data: ReadJson):  # type: ignore
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(  # type: ignore
            token,
            {"type":  "card.read", **data},
        )
        
    except Exception as e:
        pass


class CardReadExeConsumer(AsyncWebsocketConsumer):

    user: User
    token: str

    async def auth_user(self) -> bool:
        try:
            user: User = self.user
            managerFlag = await sync_to_async(is_manager)(user)
            authFlag = await sync_to_async(is_authenticated)(user)
            
            return bool(managerFlag and authFlag)
        except Exception as e:
            return False
    
    async def auth_token(self) -> bool:
        try:
            async with AsyncRedisConnection(RedisDataBase.CARD_READ_TOKEN) as redis:
                data: WriteToken | ReadToken = await redis.getDict(self.token) # type: ignore
                
                processing = data.get("processing", None)
                ID = data.get("ID", -1)
                
                if (not isinstance(processing, bool)) or (isinstance(processing, bool) and (processing is not True)):
                    raise TokenExpired()
                
                user = await User.objects.aget(id=ID)
                
                return (self.user.id == user.id)
            
        except Exception as e:
            return False
            

    async def connect(self) -> None:
        try:
            self.token = self.scope["url_route"]["kwargs"]["token"]
            self.user = self.scope["user"]
            
            self.room_group_name = self.token
            
            tokenFlags = await self.auth_token()
            userFlags = await self.auth_user()
            
            if(not (tokenFlags and userFlags)):
                raise DenyConnection("Unauthenticated User")
            
            await self.channel_layer.group_add(self.room_group_name, self.channel_name) # type: ignore

            await self.accept()
        
        except DenyConnection as f:
            APP_LOG.write_error(LogStructure().set_error(f))
            raise f
        
        except Exception as e:
            APP_LOG.write_error(LogStructure().set_error(e))
            raise DenyConnection("Invalid URL found!")

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)  # type: ignore

    async def receive(self, text_data: str):  # type: ignore
        APP_LOG.write_error(LogStructure().set_error(Exception("No Entry Here")))
        
    async def card_read(self, event: ReadJson):
        status = event["status"]
        cardID = event["card"]
        data = event["data"]
        message = event["data"]
        context: dict = {}
        
        match(status):
            case "true":
                
                try:
                    card = await Card.objects.aget(cardID=cardID)
                    
                    decrypted = EncryptData(**decrypt_data(decrypt_key(card.decryption_key).encode(), data))
                    
                    for img, value in decrypted["images"].items():
                        decrypted["images"][img] = expand_image(value, 0, 0)
                        
                    for sem in decrypted["sem_data"].keys():
                        for column in decrypted["sem_data"][sem].keys():
                            decrypted["sem_data"][sem][column] = SemMeta(*decrypted["sem_data"][sem][column])
                    
                    context.update(decrypted)
                    setSwalAlert(context, message, "success")
                except Exception as e:
                    context["messages"] = ["Failed to parse card data!"]
                    
            case _:
                context["messages"] = ["Failed to read card data"]
                
        await self.send(
            text_data=render_to_string('Dash/HTMX/report.html',context=context), 
            close=True
        )
        