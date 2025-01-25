from django.contrib import admin
from django.urls import path, re_path
from django.conf.urls.static import static
from django.conf import settings
from .views import *

app_name = 'View'
urlpatterns = [
	path('<str:id>',default_view,name='table'),
	path('<str:id>/search/',table_query,name='search'),
	path('<str:id>/search_row/',row_view,name='search_row'),
	path('<str:id>/quick_search/',quick_query,name="suggest"),
]



