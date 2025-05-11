from django.urls import path
from .views import *

app_name = 'Login'
urlpatterns = [
	path('',login_view,name='login'),	
]
