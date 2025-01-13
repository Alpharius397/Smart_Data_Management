from django.contrib import admin
from django.urls import path, re_path
from django.conf.urls.static import static
from django.conf import settings
from .views import *

app_name = 'Excel'
urlpatterns = [
 	path('',dash_board,name='dash'),
 	path('upload/',upload_screen,name='upload'),
 	path('view/<str:id>/',data_view,name='view'),
	path('view/<str:id>/<int:index>/',verify_page,name='single'), # a single view page for final decision
	path('view/<str:id>/<int:index>/search/',single_query), # a single view page for final decision
	path('view/<str:id>/search/',table_query),
	path('view/<str:id>/<int:index>/compress/',compress_data)
	
]

