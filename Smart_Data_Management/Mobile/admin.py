from django.contrib import admin
from django.db.models import Q
from django.contrib.auth.models import User
from User.models import is_admin
from .models import razorPayment
from Card.models import Card

@admin.register(razorPayment)
class CardAdmin(admin.ModelAdmin):    
    search_fields = ('user__username',)
    search_help_text = "Search by username"
    list_display = ("user__username", "cardID__cardID","order_id", "payment_id",)
    
    def get_queryset(self, request):
        
        if(is_admin(request.user)):
            return razorPayment.objects.filter(Q(cardID__user__manager__belongs__id=request.user.admin.belongs.id))
        
        return super().get_queryset(request)
    
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        
        if (db_field.name=="user"):
            
            if(is_admin(request.user)):
                
                kwargs["queryset"] = User.objects.filter((Q(student__isnull=False)))
        
        elif(db_field.name=="cardID"):
            if(is_admin(request.user)):
                user:Admin = request.user.admin.belongs.id
                kwargs["queryset"] = Card.objects.filter(user__manager__belongs__id=request.user.admin.belongs.id)
                            
        return super().formfield_for_foreignkey(db_field, request, **kwargs)