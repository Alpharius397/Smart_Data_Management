from django.contrib import admin
from User.models import Admin, Uploader, Manager, is_admin
from django.db.models import Q
from University.models import Branch
from django.contrib.auth.models import User



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
    search_fields = ('user__username',)
    search_help_text = "Search by username"
    
    def get_queryset(self, request):
        
        if(is_admin(request.user)):
            return Manager.objects.filter(Q(belongs__id=request.user.admin.belongs.id))
        
        return super().get_queryset(request)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        
        if (db_field.name=="user"):
            
            if(is_admin(request.user)):
                user:Admin = request.user.admin.belongs.id
                kwargs["queryset"] = User.objects.filter((Q(is_staff=False)|Q(is_superuser=False))&(~(Q(uploader__isnull=False)|Q(admin__isnull=False)))&(Q(manager__belongs__id=user)))
        
        elif(db_field.name=="belongs"):

            if(is_admin(request.user)):
                user:Admin = request.user.admin.belongs.id
                kwargs["queryset"] = Branch.objects.filter(id=request.user.admin.belongs.id)
                            
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    

@admin.register(Uploader)
class UserAdmin(admin.ModelAdmin):
    list_filter = (UniversityFilter,)
    search_fields = ('user__username',)
    search_help_text = "Search by username"
    
    def get_queryset(self, request):
        
        if(is_admin(request.user)):
            return Uploader.objects.filter(Q(belongs__id=request.user.admin.belongs.id))
        
        return super().get_queryset(request)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        
        if (db_field.name=="user"):
            
            if(is_admin(request.user)):
                user:Admin = request.user.admin.belongs.id
                
                kwargs["queryset"] = User.objects.filter((Q(is_staff=False)|Q(is_superuser=False))&((~(Q(manager__isnull=False)|Q(admin__isnull=False))))&(Q(uploader__belongs__id=user)))
        
        elif(db_field.name=="belongs"):
            if(is_admin(request.user)):
                user:Admin = request.user.admin.belongs.id
                kwargs["queryset"] = Branch.objects.filter(id=request.user.admin.belongs.id)
                            
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
        
    
@admin.register(Admin)
class AdminAdmin(admin.ModelAdmin):
    list_filter = (UniversityFilter,)
    search_fields = ('user__username',)
    search_help_text = "Search by username"
    
    def get_queryset(self, request):
        
        if(is_admin(request.user)):
            return Admin.objects.filter(Q(belongs__id=request.user.admin.belongs.id))
        
        return super().get_queryset(request)
    
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        
        if (db_field.name=="user"):
            
            if(is_admin(request.user)):
                user:Admin = request.user.admin.belongs.id
                
                kwargs["queryset"] = User.objects.filter((Q(is_staff=False)|Q(is_superuser=False))&(~(Q(manager__isnull=False)|Q(uploader__isnull=False)))&(Q(admin__belongs__id=user)))
        
        elif(db_field.name=="belongs"):
            if(is_admin(request.user)):
                user:Admin = request.user.admin.belongs.id
                kwargs["queryset"] = Branch.objects.filter(id=request.user.admin.belongs.id)
                            
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
