from io import BytesIO
from django.contrib import admin  # type: ignore
from django.forms import ModelChoiceField  # type: ignore
from django.http import HttpRequest  # type: ignore
import pandas as pd
from User.models import User, get_user, is_admin
from .models import Subject, University, Institute, Branch, Color, Schema
from .forms import ColorPickerForm, SubjectUpload
from django.db.models import Q  # type: ignore
from django.db.models import Q, QuerySet  # type: ignore


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    search_help_text = "Search by University name"

    def get_queryset(self, request) -> QuerySet[University]:
        user: User = request.user

        if is_admin(user):
            return University.objects.filter(
                id=user.role.belongs.institute.university.id
            )

        elif user.is_superuser:
            return University.objects.all()

        return University.objects.none()


@admin.register(Institute)
class InstituteAdmin(admin.ModelAdmin):
    list_display = ("name", "university")
    list_filter = [
        "university",
    ]
    search_fields = ("name", "university__name")
    search_help_text = "Search by Institute or University name"

    def get_queryset(self, request) -> QuerySet[Institute]:
        user: User = request.user

        if is_admin(user):
            return Institute.objects.filter(id=user.role.belongs.institute.id)

        elif user.is_superuser:
            return Institute.objects.all()

        return Institute.objects.none()


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "institute", "institute__university")
    list_filter = ["institute", "institute__university"]
    search_fields = ("name", "institute__name", "institute__university__name")
    search_help_text = "Search by Branch or Institute or University name"

    def get_queryset(self, request) -> QuerySet[Branch]:
        user: User = request.user

        if is_admin(user):
            return Branch.objects.filter(id=user.role.belongs.id)

        elif user.is_superuser:
            return Branch.objects.all()

        return Branch.objects.none()


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "semester", "marks")
    search_fields = ("name", "semester", "code")
    search_help_text = "Search by Subject name or Semester"

    form = SubjectUpload

    fieldsets = [
        (
            None,
            {
                "fields": ["code", "name", "semester", "schema", "marks"],
            },
        ),
        (
            "Advanced options",
            {
                "classes": ["collapse"],
                "fields": ["schemaChoice", "excel_file"],
            },
        ),
    ]

    def getSchemaQuerySet(self, request: HttpRequest):
        user = get_user(request)

        if is_admin(user):
            return Schema.objects.filter(branch=user.role.belongs)

        elif user.is_superuser():
            return Schema.objects.all()

        return Schema.objects.none()

    def get_queryset(self, request: HttpRequest):
        user = get_user(request)

        if is_admin(user):
            return Subject.objects.filter(schema__branch=user.role.belongs)
        elif user.is_superuser:
            return Subject.objects.all()

        return Subject.objects.none()

    def get_form(self, request: HttpRequest, obj=None, **kwargs):
        Form: SubjectUpload = super().get_form(request, obj, **kwargs)
        Form.base_fields["schemaChoice"] = ModelChoiceField(
            queryset=self.getSchemaQuerySet(request),
            label="Choose a Schema",
            required=False,
        )
        return Form

    def save_model(self, request: HttpRequest, obj: Subject, form, change: bool):
        try:
            schemaChoice = request.POST.get("schemaChoice", "")
            excel_file = request.FILES.get("excel_file")

            if not (schemaChoice or excel_file):
                raise ValueError("Nothing here")

            if not (schemaChoice and excel_file):
                raise ValueError("Both must be filled")

        except ValueError:
            super().save_model(request, obj, form, change)


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    form = ColorPickerForm

    def get_queryset(self, request: HttpRequest):
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


@admin.register(Schema)
class SchemaAdmin(admin.ModelAdmin):
    list_display = ("name", "branch")
    list_filter = [
        "branch",
    ]
    search_fields = (
        "name",
        "branch__name",
    )
    search_help_text = "Search by Branch or Schema name"

    def get_queryset(self, request: HttpRequest):
        user = get_user(request)

        if is_admin(user):
            return Schema.objects.filter(branch=user.role.belongs)

        elif user.is_superuser():
            return Schema.objects.all()

        return Schema.objects.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        user = get_user(request)

        if db_field.name == "branch":
            kwargs["queryset"] = Branch.objects.filter(id=user.role.belongs.id)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)
