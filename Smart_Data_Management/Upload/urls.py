from django.urls import path
from .views import *

app_name = 'Upload'
urlpatterns = [
 	path('',upload_screen,name='view'),
 	path('<str:id>',edit_screen,name='view_edit'),
 	path('upload/',upload,name='upload'),
 	path('edit/',edit,name='edit'),

]



