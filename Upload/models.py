from datetime import datetime
from django.db.models import (
    CharField,
    Model,
    ForeignKey,
    AutoField,
    JSONField,
    BooleanField,
    DateTimeField,
    CASCADE,
    RESTRICT,
)  # type: ignore
from User.models import User, is_admin, is_manager, RoleType
from django import forms
import typing


class UploadTable(Model):
    id = AutoField(
        verbose_name="FileID", primary_key=True, null=False, blank=False
    )  # type: ignore
    fileName = CharField(
        max_length=255, verbose_name="File Name", null=False, blank=False, unique=True
    )  # type: ignore
    uploader = ForeignKey(
        to=User,
        on_delete=RESTRICT,
        null=False,
        blank=False,
        related_name="uploader",
        verbose_name="File Uploader",
        limit_choices_to={"role__role": RoleType.ADMIN},
    )  # type: ignore
    assigned: "AssignTable"
    data: "DataTable"

    def clean_uploaders(self):
        if not is_admin(self.uploader):
            raise forms.ValidationError(
                "Uploader must be a admin",
                code="invalid",
                params={"value": self.uploader},
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class AssignTable(Model):
    id = AutoField(
        verbose_name="AssignID", primary_key=True, null=False, blank=False
    )  # type: ignore
    fileID = ForeignKey(
        to=UploadTable,
        verbose_name="FileID",
        related_name="assigned",
        on_delete=CASCADE,
        null=False,
        blank=False,
    )  # type: ignore
    manager = ForeignKey(
        to=User,
        on_delete=RESTRICT,
        null=False,
        blank=False,
        related_name="manager",
        verbose_name="Assigned User",
        limit_choices_to={"role__role": RoleType.MANAGER},
    )  # type: ignore

    def clean_managers(self):
        if not is_manager(self.manager):
            raise forms.ValidationError(
                "Only managers can be assigned to a file",
                code="invalid",
                params={"value": self.manager},
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class DataTable(Model):
    id = AutoField(
        verbose_name="DataID", primary_key=True, null=False, blank=False
    )  # type: ignore
    fileID = ForeignKey(
        to=UploadTable,
        verbose_name="FileID",
        related_name="data",
        on_delete=CASCADE,
        null=False,
        blank=False,
    )  # type: ignore
    # semester = IntegerField(verbose_name="Semester", validators=[MinValueValidator(1, "Semester cannot be negative or zero")],null=False,blank=False)
    locked = BooleanField(
        verbose_name="Lock Status", default=False, null=False, blank=False
    )  # type: ignore

    issued = BooleanField(
        verbose_name="Issue Status", default=False, null=True, blank=False
    )  # type: ignore
    time_of_lock = DateTimeField(
        verbose_name="Time of Lock", null=True, blank=False, default=None
    )  # type: ignore
    time_of_issue = DateTimeField(
        verbose_name="Time of Issue", null=True, blank=False, default=None
    )  # type: ignore
    status = BooleanField(
        verbose_name="Feedback Status", default=None, null=True, blank=False
    )  # type: ignore
    feed = CharField(
        max_length=255, verbose_name="Feedback", null=True, blank=False, default=None
    )  # type: ignore
    data = JSONField(verbose_name="rowData", null=False, blank=False)  # type: ignore

    def update_data(self, jsonText: dict[str, typing.Any]) -> "DataTable":
        self.data = jsonText
        self.locked = False
        self.issued = False
        self.time_of_issue = None
        self.time_of_lock = None
        self.status = None
        self.feed = None

        return self
