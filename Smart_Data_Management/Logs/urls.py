from django.urls import path, re_path
from Logs.views import *

app_name = 'Logs'
urlpatterns = [
 	path('',log_board,name='logs'),
	path('<str:date>/',single_log,name="one_day"),
	path('<str:date>/search/',row_search,name="search")
]



