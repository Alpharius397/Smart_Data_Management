from django.urls import path
from .views import *

app_name = 'Login'
urlpatterns = [
	path('',login_view,name='index'),	
	path('htmx',htmx_login_view,name='htmxLogin'),	
]
