from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser
from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "email", "password1", "password2")
        error_messages = {
            "email": {
                "unique": "Este correo ya está registrado.",
            },
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["first_name"].widget.attrs.update({
            "class": "form-control form-control-user",
            "placeholder": "First Name"
        })
        self.fields["last_name"].widget.attrs.update({
            "class": "form-control form-control-user",
            "placeholder": "Last Name"
        })
        self.fields["email"].widget.attrs.update({
            "class": "form-control form-control-user",
            "placeholder": "Email Address"
        })
        self.fields["password1"].widget.attrs.update({
            "class": "form-control form-control-user",
            "placeholder": "Password",
            'autocomplete': 'new-password',
        })
        self.fields["password2"].widget.attrs.update({
            "class": "form-control form-control-user",
            "placeholder": "Repeat Password",
            'autocomplete': 'new-password',
        })
    
    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        errores = []

        if len(password) < 8:
            errores.append("La contraseña es demasiado corta. Debe tener al menos 8 caracteres.")
        if password.isdigit():
            errores.append("La contraseña no puede ser completamente numérica.")
        if password.lower() in ["12345678", "password", "contraseña", "qwerty"]:
            errores.append("La contraseña es demasiado común.")

        if errores:
            raise forms.ValidationError(errores)

        return password


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            "class": "form-control form-control-user",
            "placeholder": "Email Address"
        })
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "class": "form-control form-control-user",
            "placeholder": "Password"
        })
    )

class OTPForm(forms.Form):
    otp = forms.CharField(
        label="Código",
        max_length=6,
        widget=forms.NumberInput(attrs={
            "class": "form-control form-control-user",
            "placeholder": "Código de verificación"
        })
    )
