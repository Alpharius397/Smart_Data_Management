from django.contrib import admin
from django.urls import path, re_path
from django.conf.urls.static import static
from django.conf import settings
from .views import *

app_name = 'Manage'
urlpatterns = [
    path('',MangerOption.as_view(),name='get'),
]



