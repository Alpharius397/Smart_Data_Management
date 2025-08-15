from django.urls import path # type: ignore
from .views import register_view, htmx_register_view, insti_change, branch_change

app_name = "Register"
urlpatterns = [
    path("", register_view, name="index"),
    path("htmx", htmx_register_view, name="htmxRegister"),
    path("htmx/institute/", insti_change, name="htmxInstitute"),
    path("htmx/branch/", branch_change, name="htmxBranch"),
]
