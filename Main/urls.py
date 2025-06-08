from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("Login.urls", "Login")),
    path("user/", include("User.urls", "User")),
    path("register/", include("Register.urls", "Register")),
    path("task/", include("Task.urls", "Task")),
    path("logout/", include("Logout.urls", "Logout")),
    path("dash/", include("Dash.urls", "Dash")),
    path("table/", include("Table.urls", "Table")),
    path("report/", include("Report.urls", "Report")),
    path("logs/", include("Logs.urls", "Logs")),
    path("certificate/", include("Certificate.urls", "Certificate")),
    path("mobile/", include("Mobile.urls", "Mobile")),
]

admin.site.site_header = "System Admin"
admin.site.site_title = "Admin Portal"
admin.site.index_title = "Welcome to Smart Data Management Site"


urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(
    settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
)  # type: ignore
