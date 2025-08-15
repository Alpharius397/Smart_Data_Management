from django.forms import ModelChoiceField  # type: ignore
from django.http import HttpRequest  # type: ignore
from User.models import User, get_user, is_admin
from .models import Card
from django.contrib import admin  # type: ignore
from django.db.models import Q, QuerySet  # type: ignore


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = (
        "cardID",
        "done_by",
        "last_write",
    )
    search_fields = ("cardID", "role", "done_by__username")
    search_help_text = "Search by username or card ID"
    fieldsets = [
        (
            None,
            {
                "fields": ["cardID", "done_by", "last_write", "belongs"],
            },
        ),
    ]

    def get_queryset(self, request) -> QuerySet:
        user: User = get_user(request)

        if is_admin(user):
            return Card.objects.filter(
                Q(done_by__role__belongs__id=user.role.belongs.id)
            )

        elif user.is_superuser:
            return Card.objects.all()

        return Card.objects.none()

    def formfield_for_foreignkey(
        self, db_field, request: HttpRequest, **kwargs
    ) -> ModelChoiceField:
        user: User = get_user(request)

        if db_field.name == "done_by":
            if is_admin(user):
                kwargs["queryset"] = User.objects.filter(
                    Q(role__belongs__id=user.role.belongs.id)
                )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)
