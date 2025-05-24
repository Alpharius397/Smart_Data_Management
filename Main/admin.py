from django.contrib import admin
from User.models import Admin, UserObject
from django.db.models import Q
from User.models import is_admin
from .models import FileTable
from University.models import Branch

@admin.register(FileTable)
class CardAdmin(admin.ModelAdmin):
    search_fields = ('cardID',)
    search_help_text = "Search by card ID"
    list_display = ("uploader__username", "fileName",)
    
    def get_queryset(self, request):

        if(is_admin(request.user)):
            return FileTable.objects.filter(Q(uploader__belongs__id=request.user.admin.belongs.id))
        
        return super().get_queryset(request)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        
        if (db_field.name=="uploader"):
            
            if(is_admin(request.user)):
                user:UserObject = request.user
                branch_id:int = user.admin.belongs.id
                kwargs["queryset"] = FileTable.objects.filter(Q(uploader__belongs__id=branch_id))

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

