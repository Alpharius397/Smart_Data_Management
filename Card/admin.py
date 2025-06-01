from django.contrib import admin
from User.models import User, get_user
from django.db.models import Q
from User.models import is_admin
from .models import Card


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    search_fields = ("cardID",)
    search_help_text = "Search by card ID"
    list_display = (
        "user__username",
        "cardID",
        "data__id",
    )

    def get_queryset(self, request):
        user: User = get_user(request)

        if is_admin(user):
            return Card.objects.filter(Q(user__role__belongs__id=user.role.belongs.id))

        return super().get_queryset(request)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            if is_admin(request.user):
                user: User = request.user
                kwargs["queryset"] = User.objects.filter(
                    Q(role__belongs__id=user.role.belongs.id)
                )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)
