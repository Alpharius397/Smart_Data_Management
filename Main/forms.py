from django.forms.forms import Form
from Main.errors import NoErrorInForm
from django.forms import ValidationError


class MainForm(Form):
    def getErrors(self) -> str:
        """Helper to generate errors text"""
        if not self.errors:
            raise NoErrorInForm()

        errorText = ""

        for field, error in self.errors.items():
            if (l := self.declared_fields.get(field).label) is not None:
                errorText += f"{l}: "

            errorText += ",".join([",".join(i) for i in error.data])
            errorText += "\n"

        return errorText.rstrip("\n")


def getErrors(error: ValidationError) -> str:
    errorText = ""

    for field, errors in error.error_dict.items():
        errorText += "{0}: {1}".format(field, ",".join([",".join(i) for i in errors]))
    return errorText
