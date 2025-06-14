from django.contrib import admin  # type: ignore
from User.models import get_user, is_admin
from .models import Subject, University, Institute, Branch, Color, Schema
from .forms import ColorPickerForm
from django.db.models import Q  # type: ignore

admin.site.register(University)
admin.site.register(Institute)
admin.site.register(Branch)
admin.site.register(Subject)
admin.site.register(Schema)


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    form = ColorPickerForm

    def get_queryset(self, request):
        user = get_user(request)

        if is_admin(user):
            return Color.objects.filter(Q(institute__id=user.role.belongs.institute.id))

        elif user.is_superuser():
            return Color.objects.all()

        return Color.objects.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        user = get_user(request)
        if db_field.name == "institute":
            kwargs["queryset"] = Institute.objects.filter(
                id=user.role.belongs.institute.id
            )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)
