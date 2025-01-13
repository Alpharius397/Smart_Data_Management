from django.contrib import admin
from Excel.models import *
from django.db.models import Q
from django.conf import settings
from django.contrib.auth.models import User
    
class BelongToFilter(admin.SimpleListFilter):
    title = "Uploader"
    
    parameter_name = "belongsTo"
    
    def lookups(self, request, model_admin:admin.ModelAdmin):
        upload_user:set[tuple[str,str]] = set()

        for i in model_admin.get_queryset(request).all():
            upload_user.add((i.belongs.user.username,i.belongs.user.username))
        
        return list(upload_user)
    
    def queryset(self, request, queryset):
        if(self.value() is None): return queryset
        
        return queryset.filter(belongs__user__username=self.value())
    
class AssignedFilter(admin.SimpleListFilter):
    title = "Assigned"
    
    parameter_name = "assignedTo"
    
    def lookups(self, request, model_admin: admin.ModelAdmin):
        assign_user:set[tuple[str,str]] = set()

        for i in model_admin.get_queryset(request).all():
            if(i.assigned is None): continue
            assign_user.add((i.assigned.user.username,i.assigned.user.username))
        
        return list(assign_user)
        
    
    def queryset(self, request, queryset):
        if(self.value() is None): return queryset
        
        username = self.value()
        query = Q(assigned__user__username=username)
        
        return queryset.filter(query)
    
class MongoLookup(admin.SimpleListFilter):
    title = "Object ID"
    parameter_name = "mongo_id"
    
    
    def lookups(self, request, model_admin: admin.ModelAdmin):
        return [(i.mongo_id,i.mongo_id) for i in model_admin.get_queryset(request).all()]
    
    def queryset(self, request, queryset):
        if(self.value() is None): return queryset
        return queryset.filter(mongo_id=self.value())
    
class UserAssigned(admin.SimpleListFilter):
    title = "Task Assigned"
    
    parameter_name = "taskAssigned"
    
    def lookups(self, request, model_admin):
        return [(True,"Users Assigned"),(False,"Pending Assignment")]
    
    
    def queryset(self, request, queryset):
        
        status = self.value()
        
        if(status is None): return queryset
        
        match(status):
            case True: return queryset.filter(assigned__isnull=False)
            case False: return queryset.filter(assigned__isnull=True)

@admin.register(VerificationTable)
class VerificationFilter(admin.ModelAdmin):
    list_display = ('mongo_id','belongs','assigned')
    list_filter = (MongoLookup,BelongToFilter,AssignedFilter,UserAssigned)
    
    search_fields = ('mongo_id','belongs__username')
    search_help_text = "Search by MongoID or Uploader's Username"
    
    


