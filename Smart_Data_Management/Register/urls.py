from django.urls import path
from .views import *

app_name = 'Register'
urlpatterns = [
 	path('',register_view,name='register'),
  	path('uni/',insti_change,name='insti'),
  	path('insti/',branch_change,name='branch'),
]
