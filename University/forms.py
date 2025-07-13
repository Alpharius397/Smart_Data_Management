from io import BytesIO
from django.forms import CharField, ValidationError, Widget, ModelForm, ModelChoiceField, FileField # type: ignore
from django.db import transaction  # type: ignore
from django.core.exceptions import ValidationError # type: ignore
import pandas as pd

from constants.constants import DEFAULT_ERROR # type: ignore
from .models import ColorRegex, Schema, Subject
from django.core.files.uploadedfile import UploadedFile

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
    main_color = CharField(validators=[ColorRegex], max_length=7,min_length=7,widget=ColorPick())
    sec_color = CharField(validators=[ColorRegex], max_length=7,min_length=7,widget=ColorPick())
    
class SubjectUpload(ModelForm):
    schemaChoice = ModelChoiceField(queryset=Schema.objects.none(), label="Choose a Schema", required=False)
    excel_file = FileField(label="Excel File with semester data", required=False)
    
    def clean(self) -> None:
        cleaned_data = super().clean()
        
        try:
            schema: Schema = cleaned_data.get("schema", "")
            excel_file: UploadedFile = cleaned_data.get("excel_file")
            
            has_any = schema or excel_file
            has_all = schema and excel_file

            if has_any and not has_all:
                raise ValidationError(
                    "If you fill any of the optional fields (Schema Choice, Excel File), you must fill both."
                )

            NEEDED = set(["name", "semester", "marks"])
            
            subjectList: list[Subject] = []
            
            with transaction.atomic(), excel_file.open() as file:
                data = pd.read_excel(BytesIO(file.read()))
                
                data.rename(columns={col: col.lower() for col in data.columns}, inplace=True)
                
                assert all([(col in NEEDED) for col in data.columns]), f"Invalid Columns Detected! Allowed columns: {', '.join(NEEDED)}"
            
                mapping = {"name": -1, "semester": -1, "marks": -1}

                for idx, column in enumerate(data.columns):
                    if(column in NEEDED): mapping[column] = idx
            
                for row in data.itertuples():
                    name = row[mapping["name"]]
                    semester = row[mapping["semester"]]
                    marks = row[mapping["marks"]]
                    
                    subjectList.append(Subject(schema=schema, semester=semester, name=name, marks=marks))
                
                Subject.objects.bulk_create(subjectList)
            
        except AssertionError as e:
            raise ValidationError(e)
        
        except Schema.DoesNotExist:
            raise ValidationError("Schema does not exists")
            
        except ValidationError as f:
            raise f
        
        except Exception as e:
            raise ValidationError(DEFAULT_ERROR)

        return cleaned_data