from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings
from .views import *

app_name = 'Excel'
urlpatterns = [
 	path('',dash_board,name='dash'),
 	path('upload/',upload_screen,name='upload'),
 	path('view/belongs/<str:id>/',owner_view,name='owner_view'),
 	path('view/assign/<str:id>/',assign_view,name='assign_view'),

]
