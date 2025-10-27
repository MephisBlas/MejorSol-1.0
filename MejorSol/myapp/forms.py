# myapp/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Perfil


class RegistroForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Correo Electrónico")
    first_name = forms.CharField(required=True, label="Nombre")
    last_name = forms.CharField(required=True, label="Apellido")
    telefono = forms.CharField(required=False, label="Teléfono")
    direccion = forms.CharField(
        required=False,
        label="Dirección",
        widget=forms.Textarea(attrs={"rows": 3})
    )

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "password1", "password2"]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está registrado.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]

        if commit:
            user.save()
            # Crear o actualizar el perfil asociado
            perfil, _ = Perfil.objects.get_or_create(usuario=user)
            perfil.telefono = self.cleaned_data.get("telefono", "")
            perfil.direccion = self.cleaned_data.get("direccion", "")
            perfil.save()

        return user


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(label="Nombre", max_length=30, required=False)
    last_name  = forms.CharField(label="Apellido", max_length=30, required=False)
    email      = forms.EmailField(label="Correo", required=False)

    class Meta:
        model  = User
        fields = ["first_name", "last_name", "email"]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            # Evita duplicar correos al editar el perfil
            qs = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("Este correo ya está en uso.")
        return email
