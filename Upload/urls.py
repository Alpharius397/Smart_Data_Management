from django.urls import path
from .views import upload_screen, edit_screen, delete_screen, upload, edit, delete

app_name = "Upload"
urlpatterns = [
    path("", upload_screen, name="view"),
    path("edit/<int:id>/", edit_screen, name="view_edit"),
    path("delete/<int:id>", delete_screen, name="view_delete"),
    path("upload/", upload, name="upload"),
    path("<int:id>/edit/", edit, name="edit"),
    path("<int:id>/delete/", delete, name="delete"),
]
