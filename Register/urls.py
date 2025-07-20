from django.urls import path
from .views import *

app_name = 'Register'
urlpatterns = [
 	path('',register_view,name='index'),
 	path('htmx',htmx_register_view,name='htmxRegister'),
  	path('htmx/institute/',insti_change,name='htmxInstitute'),
  	path('htmx/branch/',branch_change,name='htmxBranch'),
	path('htmx/mobile/institute/',insti_change_mobile, name='htmxMobileInstitute'),
  	path('htmx/mobile/branch/',branch_change_mobile, name='htmxMobileBranch'),
]
