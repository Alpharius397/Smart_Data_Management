from django.contrib import admin
from User.models import is_admin
from .models import *
from .forms import ColorPickerForm
from django.db.models import Q

admin.site.register(University)
admin.site.register(Institute)
admin.site.register(Branch)
admin.site.register(Subjects)


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    form = ColorPickerForm
    
    def get_queryset(self, request):
        
        if(is_admin(request.user)):
            return Color.objects.filter(Q(institute__id=request.user.branch.institute.id))
        
        return super().get_queryset(request)