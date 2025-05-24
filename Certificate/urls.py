from django.urls import path
from .views import *

app_name = 'Certificate'
urlpatterns = [
 	path('<str:certificate>/<str:cardID>/',certificate_check,name='__check'),
 	path('<str:certificate>/<str:cardID>/load',loadCertificate,name='certi'),
]



