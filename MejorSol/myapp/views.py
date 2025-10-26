# myapp/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

import json
import uuid
import random

from .forms import RegistroForm
from .models import ChatConversation, ChatMessage

# ===========================
#        PÚBLICO / AUTH
# ===========================

def index(request):
    return render(request, 'index.html')

def productos(request):
    return render(request, 'Productos.html')

def is_admin(user):
    return user.is_staff or user.is_superuser

def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'¡Registro exitoso! Bienvenido {user.first_name}.')
                return redirect('admin_panel' if (user.is_staff or user.is_superuser) else 'client_dashboard')
    else:
        form = RegistroForm()
    return render(request, 'registro.html', {'form': form})

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    def form_valid(self, form):
        super().form_valid(form)
        return redirect('admin_panel' if (self.request.user.is_staff or self.request.user.is_superuser) else 'client_dashboard')

@login_required
@user_passes_test(is_admin)
def admin_panel(request):
    return render(request, 'admin/admin_panel.html', {'user': request.user})

@login_required
def client_dashboard(request):
    return render(request, 'cliente/client_dashboard.html', {'user': request.user})

def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('admin_panel' if (user.is_staff or user.is_superuser) else 'client_dashboard')
        messages.error(request, 'Usuario o contraseña incorrectos.')
    return render(request, 'registration/login.html')

# ===========================
#          CHATBOT
# ===========================

def chatbot_demo(request):
    return render(request, 'chatbot/chatbot_demo.html')

class FreeChatBotService:
    def __init__(self):
        self.kits_solares = {
            'ongrid': {
                '1kw':  {'nombre': 'Kit Panel Solar 1.0 KW OnGrid','precio': '$1.500.000','ahorro_mensual': '$15.000 a $20.000','caracteristicas': ['Instalado con tramitación SEC','Sistema NetBilling','Ideal para viviendas pequeñas','Pago en cuotas con cualquier tarjeta']},
                '1.5kw':{'nombre': 'Kit Panel Solar 1.5 KW OnGrid','precio': '$1.900.000','ahorro_mensual': '$25.000 a $30.000','caracteristicas': ['Instalado con tramitación SEC','Sistema NetBilling','Perfecto para familias pequeñas','Pago en cuotas con cualquier tarjeta']},
                '2kw':  {'nombre': 'Kit Panel Solar 2.0 KW OnGrid','precio': '$2.300.000','ahorro_mensual': '$28.000 a $40.000','caracteristicas': ['Instalado con tramitación SEC','Sistema NetBilling','Para consumo medio residencial','Pago en cuotas con cualquier tarjeta']},
                '3kw':  {'nombre': 'Kit Panel Solar 3.0 KW OnGrid','precio': '$3.400.000','ahorro_mensual': '$40.000 a $50.000','caracteristicas': ['Instalado con tramitación SEC','Sistema NetBilling','Ideal para familias medianas','Pago en cuotas con cualquier tarjeta']},
                '4kw':  {'nombre': 'Kit Panel Solar 4.0 KW OnGrid','precio': '$3.900.000','ahorro_mensual': '$60.000','caracteristicas': ['Instalado con tramitación SEC','Sistema NetBilling','Para consumo alto residencial','Pago en cuotas con cualquier tarjeta']},
                '5kw':  {'nombre': 'Kit Panel Solar 5.0 KW OnGrid','precio': '$5.300.000','ahorro_mensual': '$65.000 a $85.000','caracteristicas': ['Instalado con tramitación SEC','Sistema NetBilling','Para viviendas grandes','Pago en cuotas con cualquier tarjeta']},
            },
            'offgrid': {
                '5kw': {'nombre': 'Kit OffGrid 5KW F1 Litio','precio': '$3.900.000','caracteristicas': ['Autonomía nocturna de 3 a 5 horas','Instalación bajo norma SEC','2.200 watts en paneles','Respaldo en baterías 4.8KW/h','Inversor HPPT 5.200 watts']},
                '6kw': {'nombre': 'Kit OffGrid 6KW F1 Litio','precio': '$4.220.000','caracteristicas': ['Autonomía nocturna de 4 a 6 horas','Instalación bajo norma SEC','5.300 watts en paneles','Respaldo en baterías 5.2KW/h','Inversor HPPT 8.000 watts']},
                '8kw': {'nombre': 'Kit OffGrid 8KW F1 Litio','precio': '$6.640.000','caracteristicas': ['Autonomía nocturna de 6 a 8 horas','Instalación bajo norma SEC','4.400 watts en paneles','Respaldo en baterías 9.6KW/h','Inversor HPPT 8.000 watts']},
                '10kw':{'nombre': 'Kit OffGrid 10KW F1 Litio','precio': '$7.550.000','caracteristicas': ['Autonomía nocturna de 7 a 9 horas','Instalación bajo norma SEC','5.600 watts en paneles','Respaldo en baterías 9.6KW/h','Inversor HPPT 10.000 watts']},
            }
        }

    def get_kit_info(self, tipo, capacidad):
        try:
            kit = self.kits_solares[tipo][capacidad]
            resp = f"📊 **{kit['nombre']}**\n\n💵 **Precio:** {kit['precio']}\n"
            if 'ahorro_mensual' in kit:
                resp += f"💰 **Ahorro mensual:** {kit['ahorro_mensual']}\n"
            resp += "\n🔧 **Características:**\n" + "\n".join(f"✅ {c}" for c in kit['caracteristicas'])
            resp += "\n\n📞 **Contacto:** +56 9 8152 0994"
            return resp
        except KeyError:
            return "No tengo información de ese kit específico. ¿Podrías ser más específico?"

    def get_offgrid_general_info(self):
        return ("🏠 **Kits OffGrid - Energía Autónoma**\n\n"
                "Sistemas independientes de la red eléctrica. Ideales para:\n"
                "✅ Zonas sin conexión a red\n✅ Backup de energía\n✅ Propiedades rurales\n\n"
                "**Capacidades disponibles:**\n"
                "🔸 5KW - $3.900.000\n🔸 6KW - $4.220.000\n🔸 8KW - $6.640.000\n🔸 10KW - $7.550.000\n\n"
                "¿Te interesa alguna capacidad específica?")

    def get_general_solar_info(self):
        return ("☀️ **Energía Solar en Chile**\n\n"
                "Beneficios: Ahorro, ROI 3-5 años, energía limpia, +valor propiedad, independencia.\n"
                "Vida útil paneles 25-30 años, mantenimiento mínimo.")

    def get_ongrid_offgrid_comparison(self):
        return ("🔌 **OnGrid vs OffGrid**\n\n"
                "**OnGrid:** Inyecta a la red, sin baterías, ideal urbano, NetBilling.\n"
                "**OffGrid:** Independiente, con baterías, ideal rural, backup cortes.")

    def get_contact_info(self):
        return ("📞 **Contacto SIEER Chile**\n\n"
                "WhatsApp: +56 9 8152 0994 • Web: sieer.cl • L-V 9:00-18:00")

    def get_greeting(self):
        return "¡Hola! 👋 Soy SIEERBot. ¿Buscas info de kits, precios o instalación?"

    def get_farewell(self):
        return "¡Gracias por tu consulta! 🌞 Escríbenos al +56 9 8152 0994 o sieer.cl"

    def get_default_response(self):
        return random.choice([
            "¿Buscas OnGrid u OffGrid? También puedo hablar de precios, instalación y financiamiento.",
            "No entendí del todo. ¿Puedes reformular? Puedo ayudarte con kits, paneles, inversores o baterías.",
        ])

    def get_ai_response(self, user_message, history=None):
        msg = user_message.lower()
        if any(x in msg for x in ['1kw', '1 kw']):  return self.get_kit_info('ongrid','1kw')
        if any(x in msg for x in ['1.5kw']):         return self.get_kit_info('ongrid','1.5kw')
        if any(x in msg for x in ['2kw', '2 kw']):   return self.get_kit_info('ongrid','2kw')
        if any(x in msg for x in ['3kw', '3 kw']):   return self.get_kit_info('ongrid','3kw')
        if any(x in msg for x in ['4kw', '4 kw']):   return self.get_kit_info('ongrid','4kw')
        if any(x in msg for x in ['5kw']) and 'offgrid' not in msg: return self.get_kit_info('ongrid','5kw')
        if any(x in msg for x in ['offgrid', 'off grid', 'autónomo']):
            if '5kw' in msg:  return self.get_kit_info('offgrid','5kw')
            if '6kw' in msg:  return self.get_kit_info('offgrid','6kw')
            if '8kw' in msg:  return self.get_kit_info('offgrid','8kw')
            if '10kw' in msg: return self.get_kit_info('offgrid','10kw')
            return self.get_offgrid_general_info()
        if any(x in msg for x in ['panel solar','paneles solares','energía solar']): return self.get_general_solar_info()
        if any(x in msg for x in ['ongrid vs offgrid','diferencia']): return self.get_ongrid_offgrid_comparison()
        if any(x in msg for x in ['contacto','teléfono','whatsapp','ubicación']):   return self.get_contact_info()
        if any(x in msg for x in ['hola','buenas','saludos']):                       return self.get_greeting()
        if any(x in msg for x in ['adiós','chao','gracias','hasta luego']):          return self.get_farewell()
        return self.get_default_response()

@csrf_exempt
@require_POST
def send_message(request):
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')
        session_id = data.get('session_id') or str(uuid.uuid4())
        bot = FreeChatBotService()
        return JsonResponse({'status':'success','response':bot.get_ai_response(user_message),'session_id':session_id})
    except Exception as e:
        return JsonResponse({'status':'error','response':'Lo siento, ocurrió un error. Intenta nuevamente.','error':str(e)})

def get_conversation_history(request, session_id):
    try:
        conv = ChatConversation.objects.get(session_id=session_id)
        msgs = ChatMessage.objects.filter(conversation=conv)
        history = [{'message': m.message, 'is_bot': m.is_bot, 'timestamp': m.timestamp.isoformat()} for m in msgs]
        return JsonResponse({'history': history})
    except ChatConversation.DoesNotExist:
        return JsonResponse({'history': []})

# ===========================
#     COTIZACIONES (DEMO)
# ===========================

# Datos demo en memoria (puedes reemplazar por tu modelo después)
COTIZACIONES = [
    {"id": 1, "cliente": "Juan Pérez", "fecha": "2025-10-20", "total": 250000, "estado": "Pendiente"},
    {"id": 2, "cliente": "Empresa SolarTech", "fecha": "2025-10-21", "total": 480000, "estado": "Aprobada"},
]

# Catálogo demo de kits (usado tanto en CREAR como en EDITAR)
KITS_DICT = {
    "ongrid": [
        {"id": 1, "nombre": "Kit On-Grid 1 kW", "precio": 1500000, "potencia": 1.0},
        {"id": 2, "nombre": "Kit On-Grid 2 kW", "precio": 2300000, "potencia": 2.0},
        {"id": 3, "nombre": "Kit On-Grid 3 kW", "precio": 3400000, "potencia": 3.0},
        {"id": 4, "nombre": "Kit On-Grid 4 kW", "precio": 3900000, "potencia": 4.0},
        {"id": 5, "nombre": "Kit On-Grid 5 kW", "precio": 5300000, "potencia": 5.0},
    ],
    "offgrid": [
        {"id": 101, "nombre": "Kit Off-Grid 5 kW Litio", "precio": 3900000, "potencia": 5.0},
        {"id": 102, "nombre": "Kit Off-Grid 6 kW Litio", "precio": 4220000, "potencia": 6.0},
        {"id": 103, "nombre": "Kit Off-Grid 8 kW Litio", "precio": 6640000, "potencia": 8.0},
        {"id": 104, "nombre": "Kit Off-Grid 10 kW Litio", "precio": 7550000, "potencia": 10.0},
    ],
}

KWH_TABLE = [
    {"kwh": 300, "sugerencia": "Kit On-Grid 1–2 kW"},
    {"kwh": 500, "sugerencia": "Kit On-Grid 3 kW"},
    {"kwh": 700, "sugerencia": "Kit On-Grid 4–5 kW"},
    {"kwh": 1200, "sugerencia": "Kit Off-Grid 6–10 kW"},
]

@login_required
@user_passes_test(is_admin)
def cotizaciones_view(request):
    return render(request, "admin/cotizaciones.html", {"cotizaciones": COTIZACIONES})

@login_required
@user_passes_test(is_admin)
def crear_cotizacion(request):
    if request.method == "POST":
        nuevo = {
            "id": len(COTIZACIONES) + 1,
            "cliente": request.POST.get("cliente", "").strip(),
            "fecha": request.POST.get("fecha", ""),
            "total": request.POST.get("total", "0"),
            "estado": request.POST.get("estado", "Pendiente"),
            # opcionalmente podrías guardar "tipo_sistema" y "kit_id"
            "tipo_sistema": request.POST.get("tipo_sistema"),
            "kit_id": request.POST.get("kit_id"),
        }
        COTIZACIONES.append(nuevo)
        return redirect("cotizaciones")

    context = {
        "kits_json": json.dumps(KITS_DICT, ensure_ascii=False),
        "kwh_json": json.dumps(KWH_TABLE, ensure_ascii=False),
    }
    return render(request, "admin/crear_cotizacion.html", context)

@login_required
@user_passes_test(is_admin)
def ver_cotizacion(request, cot_id):
    cot = next((c for c in COTIZACIONES if c["id"] == int(cot_id)), None)
    if not cot:
        return HttpResponse("Cotización no encontrada.", status=404)
    return render(request, "admin/ver_cotizacion.html", {"cot": cot})

@login_required
@user_passes_test(is_admin)
def editar_cotizacion(request, cot_id):
    """
    IMPORTANTE: enviamos 'kits_json' y 'kwh_json' IGUAL que en CREAR,
    para que el template de editar rellene el <select> de kits.
    """
    cot = next((c for c in COTIZACIONES if c["id"] == int(cot_id)), None)
    if not cot:
        return HttpResponse("Cotización no encontrada.", status=404)

    if request.method == "POST":
        cot["cliente"] = request.POST.get("cliente", "").strip()
        cot["fecha"] = request.POST.get("fecha", "")
        cot["total"] = request.POST.get("total", "0")
        cot["estado"] = request.POST.get("estado", cot.get("estado", "Pendiente"))
        # también puedes actualizar tipo_sistema / kit_id si tu form los envía:
        cot["tipo_sistema"] = request.POST.get("tipo_sistema", cot.get("tipo_sistema"))
        cot["kit_id"] = request.POST.get("kit_id", cot.get("kit_id"))
        return redirect("cotizaciones")

    context = {
        "cot": cot,
        "kits_json": json.dumps(KITS_DICT, ensure_ascii=False),
        "kwh_json": json.dumps(KWH_TABLE, ensure_ascii=False),
    }
    return render(request, "admin/editar_cotizacion.html", context)

@login_required
@user_passes_test(is_admin)
def eliminar_cotizacion(request, cot_id):
    cot = next((c for c in COTIZACIONES if c["id"] == int(cot_id)), None)
    if not cot:
        return HttpResponse("Cotización no encontrada.", status=404)
    if request.method == "POST":
        COTIZACIONES.remove(cot)
        return redirect("cotizaciones")
    return render(request, "admin/eliminar_cotizacion.html", {"cot": cot})
