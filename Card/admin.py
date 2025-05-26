from django.contrib import admin
from User.models import _User as User
from django.db.models import Q
from User.models import is_admin
from .models import *

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    search_fields = ('cardID',)
    search_help_text = "Search by card ID"
    list_display = ("user__username", "cardID", "rowIndex", "mongoID",)
    
    
    def get_queryset(self, request):
        user:User = request.user
        
        if(is_admin(request.user)):
            return Card.objects.filter(Q(user__manager__belongs__id=request.user.admin.belongs.id))
        
        return super().get_queryset(request)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        
        if (db_field.name=="user"):
            
            if(is_admin(request.user)):
                user:User = request.user
                kwargs["queryset"] = User.objects.filter(Q(role__belongs__id=user.role.belongs.id))

        return super().formfield_for_foreignkey(db_field, request, **kwargs)