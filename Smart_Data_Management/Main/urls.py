from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
	path('admin/', admin.site.urls),
	path('',include('Login.urls','Login')),
	path('register/',include('Register.urls','Register')),
	path('excel/',include('Excel.urls','Excel')),
	path('logout/',include('Logout.urls','Logout')),
	path('manage/',include('User.urls','Manage'))
]
admin.site.site_header = "System Admin"
admin.site.site_title = "Admin Portal"
admin.site.index_title = "Welcome to Smart Data Management Site"

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)