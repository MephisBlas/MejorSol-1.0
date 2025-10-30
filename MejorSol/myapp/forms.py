from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Perfil, Producto, Categoria

# ===========================
# FORMULARIOS DE USUARIO Y AUTENTICACIÓN
# ===========================

class RegistroForm(UserCreationForm):
    email = forms.EmailField(
        required=True, 
        label="Correo Electrónico",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'ejemplo@correo.com'
        })
    )
    first_name = forms.CharField(
        required=True, 
        label="Nombre",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu nombre'
        })
    )
    last_name = forms.CharField(
        required=True, 
        label="Apellido",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu apellido'
        })
    )
    telefono = forms.CharField(
        required=False, 
        label="Teléfono",
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+56 9 1234 5678'
        })
    )
    direccion = forms.CharField(
        required=False,
        label="Dirección",
        widget=forms.Textarea(attrs={
            "rows": 3,
            'class': 'form-control',
            'placeholder': 'Tu dirección completa'
        })
    )

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "password1", "password2"]
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de usuario único'
            }),
        }

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
            perfil, created = Perfil.objects.get_or_create(usuario=user)
            perfil.telefono = self.cleaned_data.get("telefono", "")
            perfil.direccion = self.cleaned_data.get("direccion", "")
            perfil.save()

        return user

class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        label="Nombre", 
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label="Apellido", 
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label="Correo Electrónico", 
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    telefono = forms.CharField(
        label="Teléfono",
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    direccion = forms.CharField(
        label="Dirección",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3
        })
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'perfil'):
            self.fields['telefono'].initial = self.instance.perfil.telefono
            self.fields['direccion'].initial = self.instance.perfil.direccion

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            qs = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("Este correo ya está en uso.")
        return email

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit and hasattr(user, 'perfil'):
            user.perfil.telefono = self.cleaned_data.get('telefono', '')
            user.perfil.direccion = self.cleaned_data.get('direccion', '')
            user.perfil.save()
        return user

# ===========================
# FORMULARIOS DE PRODUCTOS (SIMPLIFICADOS)
# ===========================

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la categoría'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de la categoría'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

class ProductoForm(forms.ModelForm):
    # Campo para categoría como choice field
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.filter(activo=True),
        empty_label="Seleccione una categoría",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Producto
        fields = [
            'nombre', 
            'descripcion', 
            'sku',
            'categoria',
            'precio', 
            'stock', 
            'stock_minimo', 
            'activo'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo del producto'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción detallada del producto...'
            }),
            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código SKU único (ej: PROD-001)'
            }),
            'precio': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
            'stock_minimo': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '5'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        help_texts = {
            'sku': 'Código único de identificación del producto',
            'stock_minimo': 'Stock mínimo antes de generar alerta',
        }
    
    def clean_sku(self):
        sku = self.cleaned_data.get('sku')
        if not sku:
            raise forms.ValidationError("El SKU es obligatorio.")
        
        if len(sku) < 3:
            raise forms.ValidationError("El SKU debe tener al menos 3 caracteres.")
        
        qs = Producto.objects.filter(sku__iexact=sku)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Este SKU ya existe en el sistema.")
        
        return sku.upper()

    def clean_stock_minimo(self):
        stock_minimo = self.cleaned_data.get('stock_minimo')
        if stock_minimo < 0:
            raise forms.ValidationError("El stock mínimo no puede ser negativo.")
        return stock_minimo

# ===========================
# FORMULARIOS DE BÚSQUEDA
# ===========================

class ProductoSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        label='Buscar',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, SKU o descripción...'
        })
    )
    categoria = forms.ModelChoiceField(
        required=False,
        queryset=Categoria.objects.filter(activo=True),
        empty_label='Todas las categorías',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    con_stock_bajo = forms.BooleanField(
        required=False,
        label='Solo stock bajo',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )