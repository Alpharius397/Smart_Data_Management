from django.contrib import admin
from django.http import HttpRequest# type: ignore
from Task.models import AssignTable, TaskTable
from University.models import Branch
from User.models import RoleType, User, get_user, is_admin


@admin.register(TaskTable)
class TaskAdmin(admin.ModelAdmin):
    list_filter = ["creator", "branch"]
    list_display = ["name", "creator", "branch", "semesterLimit"]
    
    def get_queryset(self, request: HttpRequest):
        user = get_user(request)
        
        if is_admin(user):
            return TaskTable.objects.filter(branch = user.role.belongs)
        
        elif user.is_superuser:
            return TaskTable.objects.all()
            
        return TaskTable.objects.none()
    
    def formfield_for_foreignkey(self, db_field, request: HttpRequest, **kwargs):
        user = get_user(request)
        
        if db_field.name == "creator":
            kwargs["queryset"] = User.objects.filter(role__belongs = user.role.belongs, role__role = RoleType.ADMIN)
        
        elif db_field.name == "branch":
            kwargs["queryset"] = Branch.objects.filter(id = user.role.belongs.id)
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
@admin.register(AssignTable)
class AssignAdmin(admin.ModelAdmin):
    list_filter = ["taskID", "manager"]
    list_display = ["taskID", "manager"]
    
    def get_queryset(self, request: HttpRequest):
        user = get_user(request)
        
        if is_admin(user):
            return AssignTable.objects.filter(taskID__branch = user.role.belongs)
        
        elif user.is_superuser:
            return AssignTable.objects.all()
            
        return AssignTable.objects.none()
    
    def formfield_for_foreignkey(self, db_field, request: HttpRequest, **kwargs):
        user = get_user(request)
        
        if db_field.name == "taskID":
            kwargs["queryset"] = TaskTable.objects.filter(branch = user.role.belongs)
        
        elif db_field.name == "manager":
            kwargs["queryset"] = User.objects.filter(role__belongs = user.role.belongs, role__role = RoleType.MANAGER)
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)