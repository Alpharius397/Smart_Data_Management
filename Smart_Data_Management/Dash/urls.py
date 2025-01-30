from django.contrib import admin
from django.urls import path, re_path
from django.conf.urls.static import static
from django.conf import settings
from Dash.views import *

app_name = 'Dash'
urlpatterns = [
 	path('',dash_board,name='dash'),
 	path('uploader/',uploader_fetch,name='upload'),
 	path('admin/uploader/',admin_upload_fetch,name='admin_upload'),
 	path('admin/manager/',admin_manage_fetch,name='admin_manage'),
 	path('manager/',manager_fetch,name='manage'),
 	path('read/',read_screen,name='read'),
	path('card_read/',read_view,name='card_read')
]



