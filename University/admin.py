from django.contrib import admin # type: ignore
from User.models import is_admin
from .models import *
from .forms import ColorPickerForm
from django.db.models import Q # type: ignore

admin.site.register(University)
admin.site.register(Institute)
admin.site.register(Branch)
admin.site.register(Subjects)


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    form = ColorPickerForm
    
    def get_queryset(self, request):
        
        user:UserObject
        if(is_admin(request.user)):
            return Color.objects.filter(Q(institute__id=request.user.role.belongs.institute.id))
        
        if(request.user.is_superuser()):
            return Color.objects.all()
        
        return Color.objects.none()
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        
        if (db_field.name=="institute"):
            
            kwargs["queryset"] = Institute.objects.filter(id=request.user.role.belongs.institute.id)
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)