from django.contrib import admin
from django.urls import path, re_path
from django.conf.urls.static import static
from django.conf import settings
from Dash.views import *
from .sockets import CardReadExeConsumer

app_name = 'Dash'
urlpatterns = [
 	path('',dash_board,name='dash'),
 	path('admin/uploader/',admin_upload_fetch,name='admin_upload'),
 	path('admin/manager/',admin_manage_fetch,name='admin_manage'),
 	path('manager/',manager_fetch,name='manage'),
 	path('read/',read_screen,name='read'),
 	path('card_read/',read_view,name='card_read'),
	path('token/read/',check_read,name='ping_read'),
	path('<str:token>/read/',get_read_data,name='read_url'),
	path('<str:token>/',(lambda : HttpResponse(status=404)),name='__base__')
]

websocket_urlpatterns = [
	path("dash/<str:token>/", CardReadExeConsumer.as_asgi())
]


