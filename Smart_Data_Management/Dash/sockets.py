import json
from User.models import is_authenticated, is_manager, UserObject
from channels.generic.websocket import AsyncWebsocketConsumer, DenyConnection
from tools.token import hash_token
from asgiref.sync import sync_to_async
from django.template.loader import render_to_string
from constants.constants import WRITE_TOKEN

class CardReadExeConsumer(AsyncWebsocketConsumer):
    
    user: UserObject
    token: str

    async def auth_user(self) -> bool:
        user: UserObject = self.user
        managerFlag = await sync_to_async(is_manager)(user)
        authFlag = await sync_to_async(is_authenticated)(user)
        return bool(managerFlag and authFlag)
    
    async def auth_token(self) -> bool:
        sessionToken = self.scope["session"].get(WRITE_TOKEN, "None")
        return bool(hash_token(sessionToken, self.user.id)==self.token)
    
    async def connect(self) -> None:
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
            self.room_group_name, {"type": "cardRead", "message": message}
        )
        
    async def cardRead(self, event):
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
                
