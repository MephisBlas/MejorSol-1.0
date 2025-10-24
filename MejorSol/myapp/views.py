from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from .forms import RegistroForm


def index(request):
    return render(request, 'index.html')


def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Autenticar automáticamente
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'¡Registro exitoso! Bienvenido {user.first_name}.')
                
                # Redirigir según el tipo de usuario
                if user.is_staff or user.is_superuser:
                    return redirect('admin_panel')
                else:
                    return redirect('client_dashboard')
    else:
        form = RegistroForm()
    return render(request, 'registro.html', {'form': form})


def productos(request):
    return render(request, 'Productos.html')


def is_admin(user):
    return user.is_staff or user.is_superuser


# Vista de login personalizada - CORREGIDA LA RUTA DEL TEMPLATE
class CustomLoginView(LoginView):
    template_name = 'registration/login.html'  # ← Ruta corregida
    
    def form_valid(self, form):
        # Llamar al método padre para hacer el login
        response = super().form_valid(form)
        
        # Verificar el tipo de usuario después del login
        if self.request.user.is_staff or self.request.user.is_superuser:
            return redirect('admin_panel')
        else:
            return redirect('client_dashboard')


@login_required
@user_passes_test(is_admin)
def admin_panel(request):
    context = {
        'user': request.user,
    }
    return render(request, 'admin/admin_panel.html', context)


@login_required
def client_dashboard(request):
    """Vista del dashboard para clientes normales"""
    context = {
        'user': request.user,
    }
    return render(request, 'cliente/client_dashboard.html', context)


# Vista de login alternativa (opcional)
def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Verificar si es administrador o cliente normal
            if user.is_staff or user.is_superuser:
                return redirect('admin_panel')
            else:
                return redirect('client_dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'registration/login.html')  # ← Ruta corregida