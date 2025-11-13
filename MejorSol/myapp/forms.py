from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory # ¡Importante!
from .models import Perfil, Producto, Categoria, ProductoAdquirido, ProductoImagen, Cotizacion # ¡Importamos Cotizacion!
from django import forms
from django.contrib.auth import get_user_model

# ===========================
# FORMULARIOS DE USUARIO Y AUTENTICACIÓN
# ===========================

class RegistroForm(UserCreationForm):
    # ... (Tu código de RegistroForm... no necesita cambios) ...
    email = forms.EmailField(required=True, label="Correo Electrónico")
    first_name = forms.CharField(required=True, label="Nombre")
    last_name = forms.CharField(required=True, label="Apellido")
    telefono = forms.CharField(required=False, label="Teléfono")
    direccion = forms.CharField(required=False, label="Dirección", widget=forms.Textarea)

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
            perfil, created = Perfil.objects.get_or_create(usuario=user)
            perfil.telefono = self.cleaned_data.get("telefono", "")
            perfil.direccion = self.cleaned_data.get("direccion", "")
            perfil.save()
        return user

class ProfileForm(forms.ModelForm):
    # ... (Tu código de ProfileForm... no necesita cambios) ...
    first_name = forms.CharField(label="Nombre", max_length=30, required=True)
    last_name = forms.CharField(label="Apellido", max_length=30, required=True)
    email = forms.EmailField(label="Correo Electrónico", required=True)
    telefono = forms.CharField(label="Teléfono", max_length=15, required=False)
    direccion = forms.CharField(label="Dirección", required=False, widget=forms.Textarea)

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
# FORMULARIOS DE PRODUCTOS (ACTUALIZADOS)
# ===========================

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion', 'activo']
        # ... (tus widgets) ...

class ProductoForm(forms.ModelForm):
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.filter(activo=True),
        empty_label="Seleccione una categoría",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    class Meta:
        model = Producto
        fields = [
            'nombre', 'descripcion', 'sku', 'categoria', 'precio', 'costo',
            'stock', 'stock_minimo', 'potencia', 'voltaje', 'dimensiones', 'icono', 'activo'
        ]
        # ... (tus widgets) ...
    # ... (tus clean methods) ...

# ===========================
# ¡NUEVO! FORMSET PARA IMÁGENES
# ===========================
ProductoImagenFormSet = inlineformset_factory(
    Producto,  # Modelo padre
    ProductoImagen,  # Modelo hijo
    fields=('imagen', 'orden', 'es_principal'),
    extra=1,
    can_delete=True,
    widgets={
        'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        'orden': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
        'es_principal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    }
)

# ===========================
# ¡NUEVO! FORMULARIO DE SOLICITUD DE COTIZACIÓN
# ===========================
class SolicitudCotizacionForm(forms.ModelForm):
    class Meta:
        model = Cotizacion  # Usa el modelo 'Cotizacion' ANTIGUO para esto
        fields = [
            'cliente_nombre', 
            'cliente_email', 
            'cliente_telefono', 
            'cliente_rut',
            'notas_cliente'
        ]
        widgets = {
            'cliente_nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu nombre completo'}),
            'cliente_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'tu.correo@ejemplo.com'}),
            'cliente_telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+56 9 1234 5678'}),
            'cliente_rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12.345.678-9'}),
            'notas_cliente': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Escríbenos sobre tu proyecto (ej: metros cuadrados, comuna, región, etc.)'}),
        }

# FORMULARIOS DE PRODUCTOS ADQUIRIDOS
# ===========================

class ProductoAdquiridoForm(forms.ModelForm):
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.filter(activo=True, estado='activo'),
        empty_label="Seleccione un producto",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    cliente = forms.ModelChoiceField(
        queryset=User.objects.filter(perfil__tipo_usuario='cliente'),
        empty_label="Seleccione un cliente",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = ProductoAdquirido
        fields = [
            'cliente',
            'producto',
            'cantidad',
            'precio_adquisicion',
            'fecha_compra',
            'fecha_instalacion',
            'garantia_meses',
            'observaciones'
        ]
        widgets = {
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': '1'
            }),
            'precio_adquisicion': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'fecha_compra': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'fecha_instalacion': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'garantia_meses': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '12'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones adicionales...'
            }),
        }
        help_texts = {
            'precio_adquisicion': 'Precio al que se adquirió el producto (puede ser diferente al precio actual)',
            'garantia_meses': 'Meses de garantía del producto',
        }

    def clean_precio_adquisicion(self):
        precio = self.cleaned_data.get('precio_adquisicion')
        if precio and precio < 0:
            raise forms.ValidationError("El precio de adquisición no puede ser negativo.")
        return precio

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad and cantidad < 1:
            raise forms.ValidationError("La cantidad debe ser al menos 1.")
        return cantidad

    def clean(self):
        cleaned_data = super().clean()
        fecha_compra = cleaned_data.get('fecha_compra')
        fecha_instalacion = cleaned_data.get('fecha_instalacion')
        
        if fecha_instalacion and fecha_compra:
            if fecha_instalacion < fecha_compra:
                raise forms.ValidationError({
                    'fecha_instalacion': 'La fecha de instalación no puede ser anterior a la fecha de compra.'
                })
        
        return cleaned_data

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

class ProductoAdquiridoSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        label='Buscar',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por cliente o producto...'
        })
    )
    cliente = forms.ModelChoiceField(
        required=False,
        queryset=User.objects.filter(perfil__tipo_usuario='cliente'),
        empty_label='Todos los clientes',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    garantia_activa = forms.BooleanField(
        required=False,
        label='Solo garantías activas',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

# ===========================
# ¡NUEVO! FORMULARIO DE SOLICITUD DE COTIZACIÓN
# ===========================
class SolicitudCotizacionForm(forms.ModelForm):
    class Meta:
        model = Cotizacion  # Usa tu modelo 'Cotizacion'
        # ¡Estos son los campos que le pediremos al cliente!
        fields = [
            'cliente_nombre', 
            'cliente_email', 
            'cliente_telefono', 
            'cliente_rut',
            'notas_cliente' # Para que el cliente escriba un mensaje
        ]
        widgets = {
            'cliente_nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu nombre completo'
            }),
            'cliente_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'tu.correo@ejemplo.com'
            }),
            'cliente_telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+56 9 1234 5678'
            }),
            'cliente_rut': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '12.345.678-9'
            }),
            'notas_cliente': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Escríbenos sobre tu proyecto (ej: metros cuadrados, comuna, región, etc.)'
            }),
        }


User = get_user_model()


class ClienteProfileForm(forms.ModelForm):
    # Campos extra que NO están en User, sino en Perfil
    telefono = forms.CharField(label="Teléfono", max_length=15, required=False)
    direccion = forms.CharField(
        label="Dirección",
        required=False,
        widget=forms.Textarea
    )

    class Meta:
        model = User
        # Solo incluimos campos que SÍ existen en User
        fields = ["first_name", "last_name", "email"]
        labels = {
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": "Correo electrónico",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si el usuario tiene perfil, precargamos teléfono y dirección
        if self.instance and hasattr(self.instance, "perfil"):
            self.fields["telefono"].initial = self.instance.perfil.telefono
            self.fields["direccion"].initial = self.instance.perfil.direccion

    def save(self, commit=True):
        # Guardamos datos básicos del usuario
        user = super().save(commit=commit)

        # Guardamos/creamos el perfil con teléfono y dirección
        if commit:
            perfil, created = Perfil.objects.get_or_create(usuario=user)
            perfil.telefono = self.cleaned_data.get("telefono", "")
            perfil.direccion = self.cleaned_data.get("direccion", "")
            perfil.save()

        return user