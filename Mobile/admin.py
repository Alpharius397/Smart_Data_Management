from django.contrib import admin # type: ignore
from User.models import RoleType, get_user, is_admin, User
from .models import razorPayment
from Card.models import Card

@admin.register(razorPayment)
class CardAdmin(admin.ModelAdmin):    
    search_fields = ('user__username',)
    search_help_text = "Search by username"
    list_display = ("user__username", "cardID__cardID","order_id", "payment_id",)
    
    def get_queryset(self, request):
        user = get_user(request)
        
        if(is_admin(user)):
            return razorPayment.objects.filter(user__role__belongs__id=user.role.belongs.id)
        elif user.is_superuser:
            return razorPayment.objects.all()
        
        return razorPayment.objects.none()
        
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        user = get_user(request) # type: ignore
        
        if (db_field.name=="user"):
            kwargs["queryset"] = User.objects.filter(role__role = RoleType.STUDENT.value, role__belongs__id = user.role.belongs.id)
        
        elif(db_field.name=="cardID"):
            if(is_admin(request.user)): # type: ignore
                kwargs["queryset"] = Card.objects.filter(belongs__id=user.role.belongs.id)
            elif user.is_superuser:
                kwargs["queryset"] = Card.objects.all()
                
        return super().formfield_for_foreignkey(db_field, request, **kwargs)