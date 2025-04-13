from django.urls import path
from .views import *

app_name = 'User'
urlpatterns = [
 	path('',account_view,name='index'),
 	path('change/username/',change_username,name='userChange'),
 	path('change/email/',change_email,name='mailChange'),
 	path('change/password/',change_pass,name='passChange'),
	path('auth/login/',mobile_login,name='mobLogin'),
	path('auth/register/',mobile_register,name='mobRegister'),
	path('auth/refresh/',mobile_refresh,name='mobFresh'),
]



