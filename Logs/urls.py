from django.urls import path
from Logs.views import *

app_name = 'Logs'
urlpatterns = [
	path('',log_board,name='index'),
	path('<int:year>/<int:month>/<int:day>/',single_log,name="oneDay"),
 
	path("htmx/", get_logs, name="htmxLogs"),
	path('htmx/<int:year>/<int:month>/<int:day>/',search_log, name="htmxOneDay"),
]



