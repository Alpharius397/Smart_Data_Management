from django.contrib import admin
from .models import *
from django.db.models import Q

class UniversityFilter(admin.SimpleListFilter):
    title = "University"
    
    parameter_name = "uni"
    
    def lookups(self, request, model_admin: admin.ModelAdmin):
        assign_user:set[tuple[str,str]] = set()

        for i in model_admin.get_queryset(request).all():
            assign_user.add((i.belongs.institute.university.id,i.belongs.institute.university.name))
        
        return list(assign_user)
        
    
    def queryset(self, request, queryset):
        if(self.value() is None): return queryset
        
        id = self.value()
        
        query = Q()
        
        if(id):
            query = query | Q(belongs__institute__university__id=id)
        
        return queryset.filter(query)

@admin.register(Manager)
class ManagerAdmin(admin.ModelAdmin):
    list_filter = (UniversityFilter,)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name=="user"):
            kwargs["queryset"] = User.objects.filter((Q(is_staff=False)|Q(is_superuser=False))&(~Q(uploader__isnull=False)))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    
@admin.register(Uploader)
class ManagerAdmin(admin.ModelAdmin):
    list_filter = (UniversityFilter,)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name=="user"):
            kwargs["queryset"] = User.objects.filter((Q(is_staff=False)|Q(is_superuser=False))&(~Q(manager__isnull=False)))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    