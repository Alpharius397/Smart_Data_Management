from django.contrib import admin# type: ignore
from Task.models import TaskTable

admin.site.register(TaskTable)