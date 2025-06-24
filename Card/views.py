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
from tools.encrypt import encrypt_data, decrypt_data
from tools.url_auth import (
    is_auth_post,
    api_key_required,
    auth_needed,
    task_permission_check,
    token_check,
)
from Logs.loggers import APP_LOG, LogStructure, Task
from tools.utils import get_2_value, setSwalAlert
from django.views.decorators.csrf import csrf_exempt  # type: ignore
from Card.models import Card
from django.db import transaction
from django.utils import timezone
from constants.constants import DEFAULT_ERROR, WRITE_TOKEN
from Main.models import RedisConnection
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

@csrf_exempt
@api_key_required
@token_check
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
            
            sem_dict = Subject.getSubjects(schema, post["branch"])
                
            post = get_post_id(user)
            sem_dict = Subject.getSubjects(schema, post["branch"])
            
            report_data = getReport(sem_dict, task, id, idx, True)
            context.update(get_post(user))
            context.update(report_data)
            
            encrypted = encrypt_data(settings.KEY, context)
            
            with open("/home/omnissiah/Project/nodejs/react/Smart_Data_Management/sample/compress.txt", "w") as f:
                f.write(encrypted)
            
            with open("/home/omnissiah/Project/nodejs/react/Smart_Data_Management/sample/decompress.txt", "w") as f:
                f.write(json.dumps(context))
            
            
            return JsonResponse(data=FetchJson(data=encrypted), safe=True, status=200)
        except Exception as e:
            print(e)
            return JsonResponse(data=FetchJson(data=DEFAULT_ERROR), safe=True, status=500)

@csrf_exempt
@api_key_required
@token_check
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
                sem_dict = Subject.getSubjects(schema, post["branch"])
                
                issued = data["status"]
                cardID = data['card']
                
                if(not cardID):
                    raise CardIdMissing()
                
                with RedisConnection() as redis:
                    redis.unset(token)
                
                context.update({**get_post(user), **getReport(sem_dict, task, id, idx)})
                
                DataTable.set_complete_feed(task, id, idx, issued=get_2_value(issued))
                
                card, _ = Card.objects.get_or_create(cardID=cardID)
                
                card.data = context
                card.last_write = timezone.now()
                card.done_by = user
                card.save()
                cardWriteWebSocket(token, data)
                
                return JsonResponse(data={"status": "Feedback updated successfully"}, status=200)
            
        except Exception as e:
            print(e)
            return JsonResponse(data={"status": "Feedback updation failed"}, status=500)


@csrf_exempt
@api_key_required
@token_check
@auth_needed(manager_only=True)
@task_permission_check
def read_view(req: HttpRequest, id: int, idx: str, schema: int, token: str):
    user = get_user(req)
    task: TaskTable = req.__getattribute__("task")
    context: dict = {}
    if is_auth_post(req):
        
        try:
            data = ReadJson(**req.POST.dict()) # type: ignore
            
            with RedisConnection() as redis:
                redis.unset(token)
            
            
            return JsonResponse(data={"status": "Feedback updated successfully"}, status=200)
        
        except Exception as e:
            print(e)
            return JsonResponse(data={"status": "Feedback updation failed"}, status=500)
        
def cardWriteWebSocket(token: str, data: ConfirmJson):
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(token, {"type": "card.write", **data})
    except Exception as e:
        APP_LOG.write_error(LogStructure().set_description(type=Task.WEBSOCKET_FAILED, exception=e))

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
            sessionToken = self.session.get(WRITE_TOKEN, "")
            return bool(hash_token(sessionToken, self.user.id) == self.token)
        except Exception as e:
            return False
    
    async def connect(self) -> None:
        
        try:
            self.taskID = self.scope["url_route"]["kwargs"]["id"]
            self.idx = self.scope["url_route"]["kwargs"]["idx"]
            self.token = self.scope["url_route"]["kwargs"]["token"]
            self.session = self.scope["session"]
            
            self.user = self.scope["user"]
            self.room_group_name = self.token
            
            tokenFlags = await self.auth_token()
            userFlags = await self.auth_user()
            
            if(not (tokenFlags and userFlags)):
                raise DenyConnection("Unauthenticated User")
            
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)

            await self.accept()
        
        except DenyConnection as f:
            raise f
        
        except Exception as e:
            raise DenyConnection("Invalid URL found!")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data: str):
        try:
            data: ConfirmJson = ConfirmJson(**json.loads(text_data)) # type: ignore

            await self.channel_layer.group_send(
                self.room_group_name, {"type": "card.write", **data}
            )
            
        except Exception as e:
            APP_LOG.write_error(LogStructure().set_description(Task.WEBSOCKET_FAILED, taskID=str(self.taskID), manager=self.user, exception=e))
    
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
