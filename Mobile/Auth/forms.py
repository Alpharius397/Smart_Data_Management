from Main.forms import MainForm
from django import forms  # type: ignore


class LoginForm(MainForm):
    username = forms.CharField(
        max_length=100, required=True, help_text="Enter the username", label="Username"
    )

    password = forms.CharField(
        widget=forms.PasswordInput(),
        help_text="Enter the password",
        required=True,
        label="Password",
    )


class RegisterForm(MainForm):
    username = forms.CharField(
        max_length=100, required=True, help_text="Enter the username"
    )

    email = forms.EmailField(max_length=255, required=True, help_text="Enter the email")

    password = forms.CharField(
        widget=forms.PasswordInput(), help_text="Enter the password", required=True
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(), help_text="Re-enter the password", required=True
    )

    university = forms.IntegerField(
        help_text="Choose the University",
        required=True,
        label="University",
    )
    institute = forms.IntegerField(
        help_text="Choose the Institute",
        label="Institute",
        required=True,
    )

    branch = forms.IntegerField(
        help_text="Choose the Branch", label="Branch", required=True
    )

    def clean_confirm_password(self):
        password_1 = self.cleaned_data.get("password", None)
        password_2 = self.cleaned_data.get("confirm_password", None)

        if password_2 is None:
            raise forms.ValidationError(("Password cannot be empty"))

        if password_1 != password_2:
            raise forms.ValidationError(("Password cannot be different"))

        return password_2
