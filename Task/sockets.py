import json
from User.models import is_authenticated, is_manager
from channels.generic.websocket import AsyncWebsocketConsumer, DenyConnection # type: ignore
from asgiref.sync import sync_to_async, async_to_sync
from django.template.loader import render_to_string # type: ignore
from constants.constants import WRITE_TOKEN
from channels.layers import get_channel_layer # type: ignore
from Logs.loggers import APP_LOG, LogStructure, Task

def cardWriteWebSocket(token: str, message: str):
    
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(token, {"type": "cardWrite", "message": message})
    except Exception as e:
        APP_LOG.write_error(LogStructure().set_description(type=Task.WEBSOCKET_FAILED, exception=e))

class SemesterUpdate(AsyncWebsocketConsumer):
    """ TODO: Add a real-time notification when data changes """    
    
    async def connect(self) -> None:
        self.mongoID = self.scope["url_route"]["kwargs"]["id"]
        self.idx = self.scope["url_route"]["kwargs"]["idx"]
        self.token = self.scope["url_route"]["kwargs"]["token"]
        self.user = self.scope["user"]
        self.room_group_name = self.token
        
        tokenFlags = await self.auth_token()
        userFlags = await self.auth_user()
        
        if(not (tokenFlags and userFlags)):
            raise DenyConnection("Unauthenticated User")
        
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        await self.channel_layer.group_send(
            self.room_group_name, {"type": "cardWrite", "message": message}
        )
        
    async def cardWrite(self, event):
        message = event["message"]

        match(message):
            case "Done":
                await self.send(text_data=render_to_string('View/HTMX/exe/status.html',context={"status":"Data written to card successfully"}), close=True)
            case "Failed":
                await self.send(text_data=render_to_string('View/HTMX/exe/status.html',context={"status":"Data write was unsuccessfully"}), close=True)
            case "None":
                await self.send(text_data=render_to_string('View/HTMX/exe/status.html',context={"status":"Write Token Expired! Please Try Again"}), close=True)
            case _:
                await self.send(text_data=render_to_string('View/HTMX/exe/status.html',context={"status":"Something went wrong! Please Try Again"}), close=True)
                
