from django.urls import path
from .views import *

app_name = 'Mobile'
urlpatterns = [
	path('auth/login/',mobile_login,name='mobLogin'),
	path('auth/register/',mobile_register,name='mobRegister'),
	path('subscriber/',subscriber,name='subscribe'),
	
]



