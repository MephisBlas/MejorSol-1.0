# myapp/views.py
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
                return redirect('index')
    else:
        form = RegistroForm()
    return render(request, 'registro.html', {'form': form})


def productos(request):
    return render(request, 'Productos.html')


def is_admin(user):
    return user.is_staff or user.is_superuser


# Vista de login personalizada que redirige al admin_panel para administradores
class CustomLoginView(LoginView):
    template_name = 'registration/login.html'  # ← Ruta corregida
    
    def get_success_url(self):
        # Verificar si el usuario es staff o superuser
        if self.request.user.is_staff or self.request.user.is_superuser:
            return reverse_lazy('admin_panel')
        else:
            return reverse_lazy('index')


@login_required
@user_passes_test(is_admin)
def admin_panel(request):
    context = {
        'user': request.user,
    }
    return render(request, 'admin/admin_panel.html', context)