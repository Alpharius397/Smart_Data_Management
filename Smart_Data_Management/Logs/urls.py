from django.urls import path
from Logs.views import *

app_name = 'Logs'
urlpatterns = [
 	path('',log_board,name='logs'),
	path('<str:date>/',single_log,name="one_day"),
	path('<str:date>/search/',row_query,name="search"),
	path('<str:date>/search_row/',row_search,name="search_row"),
]



