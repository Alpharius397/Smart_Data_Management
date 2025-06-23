from django.urls import path
from .views import *

app_name = 'Logout'
urlpatterns = [
 	path('',logout_view,name='index'),
]
