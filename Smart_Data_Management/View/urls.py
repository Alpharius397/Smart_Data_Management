from django.contrib import admin
from django.urls import path, re_path
from django.conf.urls.static import static
from django.conf import settings
from .views import *

app_name = 'View'
urlpatterns = [
	path('<str:id>',table_view,name='table'),
	path('<str:id>/<int:idx>/',single_view,name='row'),
	path('<str:id>/search/',table_query,name='search')
]



