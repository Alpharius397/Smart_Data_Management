from django.urls import path # type: ignore
from .views import *

app_name = "Task"
urlpatterns = [
    path("<int:id>", get_task, name='index'),
    path("create/", task_create, name="create"), # Task URLS
    path("edit/<int:id>/", task_edit, name="edit"),
    path("delete/<int:id>/", task_delete, name="delete"),
    
    path("htmx/<int:id>", htmx_get_task, name='htmxIndex'), 
    path("htmx/create/", htmx_task_create, name="htmxCreate"),
    path("htmx/edit/<int:id>/", htmx_task_edit, name="htmxEdit"),
    path("htmx/delete/<int:id>/", htmx_task_delete, name="htmxDelete"),
    
    path("create/<int:id>/", sem_create, name="subCreate"), # Semester URLS
    path("edit/<int:id>/<int:idx>/", sem_edit, name="subEdit"),
    path("delete/<int:id>/<int:idx>/", sem_delete, name="subDelete"),
    
    path("htmx/create/<int:id>/", htmx_sem_create, name="htmxSubCreate"),
    path("htmx/edit/<int:id>/<int:idx>/", htmx_sem_edit, name="htmxSubEdit"),
    path("htmx/delete/<int:id>/<int:idx>/", htmx_sem_delete, name="htmxSubDelete"),
    path("htmx/assign/<int:id>", assign_form, name="htmxAssignForm"),
    path("htmx/groupBy/<int:id>", groupBy_form, name="htmxGroupBy"),
    
]
