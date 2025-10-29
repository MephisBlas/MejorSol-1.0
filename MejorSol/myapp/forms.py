# myapp/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Perfil, Producto


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

    #productos


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'nombre', 
            'descripcion', 
            'precio', 
            'stock', 
            'stock_minimo', 
            'sku', 
            'categoria', 
            'activo'  # Cambiado 'estado' por 'activo'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del producto'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del producto'
            }),
            'precio': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'stock_minimo': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código SKU único'
            }),
            'categoria': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Categoría del producto'
            }),
            'activo': forms.CheckboxInput(attrs={  # Cambiado para campo booleano
                'class': 'form-check-input'
            }),
        }
    
    def clean_sku(self):
        sku = self.cleaned_data.get('sku')
        if self.instance.pk:  # Si es una edición
            if Producto.objects.filter(sku=sku).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("Este SKU ya existe.")
        else:  # Si es creación
            if Producto.objects.filter(sku=sku).exists():
                raise forms.ValidationError("Este SKU ya existe.")
        return sku