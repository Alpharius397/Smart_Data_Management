from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings
from .views import *

app_name = 'Excel'
urlpatterns = [
 	path('',dash_board,name='dash'),
 	path('upload/',upload_screen,name='upload'),
 	path('view/<str:id>/',view_screen,name='view'),
]
