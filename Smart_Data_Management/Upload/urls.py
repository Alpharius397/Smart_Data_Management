from django.urls import path
from .views import *

app_name = 'Upload'
urlpatterns = [
	path('',upload_screen,name='view'),
	path('edit/<str:id>/',edit_screen,name='view_edit'),
	path('delete/<str:id>',delete_screen,name='view_delete'),
	path('upload/',upload,name='upload'),
	path('<str:id>/edit/',edit,name='edit'),
	path('<str:id>/delete/',delete,name='delete'),
]



