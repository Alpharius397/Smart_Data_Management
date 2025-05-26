from django.urls import path # type: ignore
from .views import *

app_name = 'User'
urlpatterns = [
 	path('',account_view,name='index'),
 	path('username/',get_username,name='username'),
 	path('email/',get_email,name='email'),
 	path('password/',get_password,name='password'),
 	path('change/username/',change_username,name='userC'),
 	path('change/email/',change_email,name='mailChange'),
 	path('change/password/',change_password,name='passChange'),
]



