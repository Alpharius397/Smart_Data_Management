from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings
from .views import *

app_name = 'Logout'
urlpatterns = [
 	path('',logout_view,name='logout'),
]
