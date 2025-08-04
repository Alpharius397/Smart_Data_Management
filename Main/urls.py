from django.contrib import admin # type: ignore
from django.urls import path, re_path, include # type: ignore
from django.conf.urls.static import static # type: ignore
from django.conf import settings # type: ignore
from Main.views import serve_media

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
    path("mobile/", include("Mobile.urls", "Mobile")),
    path("change/", include("Change.urls", "Change")),
    path("card/", include("Card.urls", "Card")),
    re_path(r"media/(?P<path>.*)$", serve_media, kwargs={"document_root": settings.MEDIA_ROOT}) # type: ignore
]

admin.site.site_header = "System Admin"
admin.site.site_title = "Admin Portal"
admin.site.index_title = "Welcome to Smart Data Management Site"
