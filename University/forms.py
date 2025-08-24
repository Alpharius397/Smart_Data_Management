from io import BytesIO
from typing import Any
from django.forms import (
    CharField,
    ValidationError,
    Widget,
    ModelForm,
    ModelChoiceField,
    FileField,
)  # type: ignore
from django.db import transaction  # type: ignore
import pandas as pd
from Logs.loggers import APP_LOG, LogStructure
from constants import DEFAULT_ERROR  # type: ignore
from .models import ColorRegex, Schema, Subject
from django.core.files.uploadedfile import UploadedFile  # type: ignore


class ColorPick(Widget):
    input_type = "color"
    template_name = "django/forms/widgets/input.html"

    def __init__(self, attrs=None):
        if attrs is not None:
            attrs = attrs.copy()
            self.input_type = attrs.pop("type", self.input_type)
        super().__init__(attrs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["type"] = self.input_type
        return context


class ColorPickerForm(ModelForm):
    main_color = CharField(
        validators=[ColorRegex], max_length=7, min_length=7, widget=ColorPick()
    )
    sec_color = CharField(
        validators=[ColorRegex], max_length=7, min_length=7, widget=ColorPick()
    )


class SubjectUpload(ModelForm):
    schemaChoice = ModelChoiceField(
        queryset=Schema.objects.none(), label="Choose a Schema", required=False
    )
    excel_file = FileField(label="Excel File with semester data", required=False)

    def clean(self) -> dict[str, Any] | None:
        cleaned_data = super().clean()

        try:
            schema: Schema = cleaned_data.get("schemaChoice", "")
            excel_file: UploadedFile = cleaned_data.get("excel_file")  # type: ignore

            has_any = schema or excel_file
            has_all = schema and excel_file

            if not (has_any or has_all):
                return cleaned_data

            if has_any and (not has_all):
                raise ValidationError(
                    "If you fill any of the optional fields (Schema Choice, Excel File), you must fill both."
                )

            NEEDED = set(["code", "name", "semester", "marks"])

            subjectList: list[Subject] = []

            with transaction.atomic(), excel_file.open() as file:
                data = pd.read_excel(BytesIO(file.read()))

                data.rename(
                    columns={col: col.lower() for col in data.columns}, inplace=True
                )

                assert all(
                    [(col in NEEDED) for col in data.columns]
                ), f"Invalid Columns Detected! Allowed columns: {', '.join(NEEDED)}"

                mapping = {"name": -1, "semester": -1, "marks": -1, "code": -1}

                for idx, column in enumerate(data.columns):
                    if column in NEEDED:
                        mapping[column] = idx

                for row in data.itertuples(index=False):
                    name = row[mapping["name"]]
                    semester = row[mapping["semester"]]
                    marks = row[mapping["marks"]]
                    code = row[mapping["code"]]

                    subjectList.append(
                        Subject(
                            schema=schema,
                            semester=semester,
                            name=name,
                            marks=marks,
                            code=code,
                        )
                    )

                Subject.objects.bulk_create(subjectList)

        except AssertionError as e:
            raise ValidationError(str(e))

        except Schema.DoesNotExist:
            raise ValidationError("Schema does not exists")

        except ValidationError as f:
            raise f

        except Exception as e:
            APP_LOG.write_error(LogStructure().set_error(e))
            raise ValidationError(DEFAULT_ERROR)

        return cleaned_data
