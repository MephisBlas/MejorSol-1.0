# views.py - CÓDIGO COMPLETO CORREGIDO
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from .forms import RegistroForm
import json
import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import render
from .models import ChatConversation, ChatMessage
import random
from django.shortcuts import render

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

# Vista de login personalizada
class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    
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
    
    return render(request, 'registration/login.html')

def chatbot_demo(request):
    """Vista para demostrar el chatbot"""
    return render(request, 'chatbot/chatbot_demo.html')

# Servicio de Chatbot Gratuito
class FreeChatBotService:
    def __init__(self):
        self.kits_solares = {
            'ongrid': {
                '1kw': {
                    'nombre': 'Kit Panel Solar 1.0 KW OnGrid',
                    'precio': '$1.500.000',
                    'ahorro_mensual': '$15.000 a $20.000',
                    'caracteristicas': [
                        'Instalado con tramitación SEC',
                        'Sistema NetBilling',
                        'Ideal para viviendas pequeñas',
                        'Pago en cuotas con cualquier tarjeta'
                    ]
                },
                '1.5kw': {
                    'nombre': 'Kit Panel Solar 1.5 KW OnGrid',
                    'precio': '$1.900.000',
                    'ahorro_mensual': '$25.000 a $30.000',
                    'caracteristicas': [
                        'Instalado con tramitación SEC',
                        'Sistema NetBilling',
                        'Perfecto para familias pequeñas',
                        'Pago en cuotas con cualquier tarjeta'
                    ]
                },
                '2kw': {
                    'nombre': 'Kit Panel Solar 2.0 KW OnGrid',
                    'precio': '$2.300.000',
                    'ahorro_mensual': '$28.000 a $40.000',
                    'caracteristicas': [
                        'Instalado con tramitación SEC',
                        'Sistema NetBilling',
                        'Para consumo medio residencial',
                        'Pago en cuotas con cualquier tarjeta'
                    ]
                },
                '3kw': {
                    'nombre': 'Kit Panel Solar 3.0 KW OnGrid',
                    'precio': '$3.400.000',
                    'ahorro_mensual': '$40.000 a $50.000',
                    'caracteristicas': [
                        'Instalado con tramitación SEC',
                        'Sistema NetBilling',
                        'Ideal para familias medianas',
                        'Pago en cuotas con cualquier tarjeta'
                    ]
                },
                '4kw': {
                    'nombre': 'Kit Panel Solar 4.0 KW OnGrid',
                    'precio': '$3.900.000',
                    'ahorro_mensual': '$60.000',
                    'caracteristicas': [
                        'Instalado con tramitación SEC',
                        'Sistema NetBilling',
                        'Para consumo alto residencial',
                        'Pago en cuotas con cualquier tarjeta'
                    ]
                },
                '5kw': {
                    'nombre': 'Kit Panel Solar 5.0 KW OnGrid',
                    'precio': '$5.300.000',
                    'ahorro_mensual': '$65.000 a $85.000',
                    'caracteristicas': [
                        'Instalado con tramitación SEC',
                        'Sistema NetBilling',
                        'Para viviendas grandes',
                        'Pago en cuotas con cualquier tarjeta'
                    ]
                }
            },
            'offgrid': {
                '5kw': {
                    'nombre': 'Kit OffGrid 5KW F1 Litio',
                    'precio': '$3.900.000',
                    'caracteristicas': [
                        'Autonomía nocturna de 3 a 5 horas',
                        'Instalación bajo norma SEC',
                        '2.200 watts en paneles',
                        'Respaldo en baterías 4.8KW/h',
                        'Inversor HPPT 5.200 watts'
                    ]
                },
                '6kw': {
                    'nombre': 'Kit OffGrid 6KW F1 Litio',
                    'precio': '$4.220.000',
                    'caracteristicas': [
                        'Autonomía nocturna de 4 a 6 horas',
                        'Instalación bajo norma SEC',
                        '5.300 watts en paneles',
                        'Respaldo en baterías 5.2KW/h',
                        'Inversor HPPT 8.000 watts'
                    ]
                },
                '8kw': {
                    'nombre': 'Kit OffGrid 8KW F1 Litio',
                    'precio': '$6.640.000',
                    'caracteristicas': [
                        'Autonomía nocturna de 6 a 8 horas',
                        'Instalación bajo norma SEC',
                        '4.400 watts en paneles',
                        'Respaldo en baterías 9.6KW/h',
                        'Inversor HPPT 8.000 watts'
                    ]
                },
                '10kw': {
                    'nombre': 'Kit OffGrid 10KW F1 Litio',
                    'precio': '$7.550.000',
                    'caracteristicas': [
                        'Autonomía nocturna de 7 a 9 horas',
                        'Instalación bajo norma SEC',
                        '5.600 watts en paneles',
                        'Respaldo en baterías 9.6KW/h',
                        'Inversor HPPT 10.000 watts'
                    ]
                }
            }
        }

    def get_kit_info(self, tipo, capacidad):
        """Obtener información específica de un kit"""
        try:
            kit = self.kits_solares[tipo][capacidad]
            respuesta = f"📊 **{kit['nombre']}**\n\n"
            respuesta += f"💵 **Precio:** {kit['precio']}\n"
            
            if 'ahorro_mensual' in kit:
                respuesta += f"💰 **Ahorro mensual:** {kit['ahorro_mensual']}\n"
            
            respuesta += "\n🔧 **Características:**\n"
            for caracteristica in kit['caracteristicas']:
                respuesta += f"✅ {caracteristica}\n"
                
            respuesta += f"\n📞 **Contacto:** +56 9 8152 0994"
            return respuesta
        except KeyError:
            return "No tengo información de ese kit específico. ¿Podrías ser más específico?"

    def get_ai_response(self, user_message, history=None):
        """Generar respuesta inteligente basada en el mensaje del usuario"""
        message_lower = user_message.lower()
        
        # Respuestas para kits OnGrid
        if any(word in message_lower for word in ['1kw', '1 kw', 'uno kilowatt']):
            return self.get_kit_info('ongrid', '1kw')
        elif any(word in message_lower for word in ['1.5kw', '1.5 kw']):
            return self.get_kit_info('ongrid', '1.5kw')
        elif any(word in message_lower for word in ['2kw', '2 kw']):
            return self.get_kit_info('ongrid', '2kw')
        elif any(word in message_lower for word in ['3kw', '3 kw']):
            return self.get_kit_info('ongrid', '3kw')
        elif any(word in message_lower for word in ['4kw', '4 kw']):
            return self.get_kit_info('ongrid', '4kw')
        elif any(word in message_lower for word in ['5kw', '5 kw']) and 'offgrid' not in message_lower:
            return self.get_kit_info('ongrid', '5kw')
            
        # Respuestas para kits OffGrid
        elif any(word in message_lower for word in ['offgrid', 'off grid', 'autónomo']):
            if '5kw' in message_lower:
                return self.get_kit_info('offgrid', '5kw')
            elif '6kw' in message_lower:
                return self.get_kit_info('offgrid', '6kw')
            elif '8kw' in message_lower:
                return self.get_kit_info('offgrid', '8kw')
            elif '10kw' in message_lower:
                return self.get_kit_info('offgrid', '10kw')
            else:
                return self.get_offgrid_general_info()
                
        # Información general
        elif any(word in message_lower for word in ['panel solar', 'paneles solares', 'energía solar']):
            return self.get_general_solar_info()
            
        # Comparación OnGrid vs OffGrid
        elif any(word in message_lower for word in ['ongrid vs offgrid', 'diferencia', 'cuál elegir']):
            return self.get_ongrid_offgrid_comparison()
            
        # Contacto y ubicación
        elif any(word in message_lower for word in ['contacto', 'teléfono', 'whatsapp', 'ubicación']):
            return self.get_contact_info()
            
        # Saludos
        elif any(word in message_lower for word in ['hola', 'buenas', 'saludos']):
            return self.get_greeting()
            
        # Despedidas
        elif any(word in message_lower for word in ['adiós', 'chao', 'gracias', 'hasta luego']):
            return self.get_farewell()
            
        # Respuesta por defecto
        else:
            return self.get_default_response()

    def get_offgrid_general_info(self):
        """Información general sobre kits OffGrid"""
        return "🏠 **Kits OffGrid - Energía Autónoma**\n\n" + \
               "Sistemas independientes de la red eléctrica. Ideales para:\n" + \
               "✅ Zonas sin conexión a red\n" + \
               "✅ Backup de energía\n" + \
               "✅ Propiedades rurales\n\n" + \
               "**Capacidades disponibles:**\n" + \
               "🔸 5KW - $3.900.000\n" + \
               "🔸 6KW - $4.220.000\n" + \
               "🔸 8KW - $6.640.000\n" + \
               "🔸 10KW - $7.550.000\n\n" + \
               "¿Te interesa alguna capacidad específica?"

    def get_general_solar_info(self):
        """Información general sobre energía solar"""
        return "☀️ **Energía Solar en Chile**\n\n" + \
               "Chile tiene una de las mejores radiaciones solares del mundo 🌍\n\n" + \
               "**Beneficios:**\n" + \
               "✅ Ahorro inmediato en cuenta de luz\n" + \
               "✅ Retorno de inversión: 3-5 años\n" + \
               "✅ Energía 100% limpia y renovable\n" + \
               "✅ Valorización de tu propiedad\n" + \
               "✅ Independencia energética\n\n" + \
               "**Datos técnicos:**\n" + \
               "🔸 Vida útil paneles: 25-30 años\n" + \
               "🔸 Eficiencia típica: 15-22%\n" + \
               "🔸 Mantenimiento: Mínimo\n" + \
               "🔸 Garantía rendimiento: 25 años"

    def get_ongrid_offgrid_comparison(self):
        """Comparación entre OnGrid y OffGrid"""
        return "🔌 **OnGrid vs OffGrid**\n\n" + \
               "**Sistema OnGrid (Conectado a Red):**\n" + \
               "✅ Inyectas excedentes a la red\n" + \
               "✅ Sin baterías = menor costo\n" + \
               "✅ Ideal zonas urbanas con red estable\n" + \
               "✅ Participas en NetBilling\n\n" + \
               "**Sistema OffGrid (Autónomo):**\n" + \
               "✅ Totalmente independiente\n" + \
               "✅ Con baterías para uso nocturno\n" + \
               "✅ Perfecto zonas rurales/sin red\n" + \
               "✅ Backup ante cortes de luz"

    def get_contact_info(self):
        """Información de contacto"""
        return "📞 **Contacto SIEER Chile**\n\n" + \
               "📍 **WhatsApp:** +56 9 8152 0994\n" + \
               "🌐 **Sitio Web:** sieer.cl\n" + \
               "💬 **Horario Atención:** Lunes a Viernes 9:00 - 18:00\n\n" + \
               "¿En qué puedo ayudarte específicamente?"

    def get_greeting(self):
        """Saludo inicial"""
        return "¡Hola! 👋 Soy SIEERBot, tu asistente especializado en energía solar.\n\n" + \
               "Puedo ayudarte con:\n" + \
               "🔸 Información de kits solares\n" + \
               "🔸 Precios y financiamiento\n" + \
               "🔸 Asesoría técnica\n" + \
               "🔸 Tramitación y legal\n\n" + \
               "¿En qué te puedo asistir hoy?"

    def get_farewell(self):
        """Mensaje de despedida"""
        return "¡Ha sido un gusto ayudarte! 🌞\n\n" + \
               "Recuerda que puedes contactarnos:\n" + \
               "📞 +56 9 8152 0994\n" + \
               "🌐 sieer.cl\n\n" + \
               "¡Que tengas un excelente día!"

    def get_default_response(self):
        """Respuesta por defecto cuando no se entiende la consulta"""
        default_responses = [
            "Interesante consulta. ¿Podrías reformularla? Estoy aquí para ayudarte con kits solares, precios, instalación y más.",
            "No estoy seguro de entender. ¿Te refieres a información sobre nuestros kits solares, precios o instalación?",
            "Como asistente especializado en energía solar, puedo ayudarte con: kits disponibles, precios, financiamiento, instalación y mantenimiento. ¿Qué te interesa?",
            "¿Te gustaría saber sobre nuestros kits OnGrid u OffGrid? También puedo ayudarte con información técnica o de financiamiento.",
            "Parece que tienes una pregunta específica. ¿Podrías contarme más? Puedo ayudarte con información sobre paneles solares, inversores, baterías o instalación."
        ]
        return random.choice(default_responses)

# VISTA DEL CHATBOT - ESTA ES LA QUE FALTABA
@csrf_exempt
@require_POST
def send_message(request):
    """API para enviar mensajes al chatbot"""
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')
        session_id = data.get('session_id', '')

        if not session_id:
            session_id = str(uuid.uuid4())

        # Usar el servicio de chatbot gratuito
        chatbot = FreeChatBotService()
        bot_response = chatbot.get_ai_response(user_message)

        return JsonResponse({
            'status': 'success',
            'response': bot_response,
            'session_id': session_id
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'response': 'Lo siento, ocurrió un error. Por favor intenta nuevamente.',
            'error': str(e)
        })

def get_conversation_history(request, session_id):
    """Obtener historial de conversación"""
    try:
        conversation = ChatConversation.objects.get(session_id=session_id)
        messages = ChatMessage.objects.filter(conversation=conversation)
        
        history = []
        for msg in messages:
            history.append({
                'message': msg.message,
                'is_bot': msg.is_bot,
                'timestamp': msg.timestamp.isoformat()
            })
        
        return JsonResponse({'history': history})
    
    except ChatConversation.DoesNotExist:
        return JsonResponse({'history': []})
    

from django.shortcuts import render, redirect
from django.http import HttpResponse

# ==============================
#      VISTAS DE COTIZACIONES
# ==============================

# Datos falsos (más adelante puedes reemplazar con un modelo real)
COTIZACIONES = [
    {"id": 1, "cliente": "Juan Pérez", "fecha": "2025-10-20", "total": 250000, "estado": "Pendiente"},
    {"id": 2, "cliente": "Empresa SolarTech", "fecha": "2025-10-21", "total": 480000, "estado": "Aprobada"},
]

# Listar cotizaciones
def cotizaciones_view(request):
    return render(request, "admin/cotizaciones.html", {"cotizaciones": COTIZACIONES})

import json

def crear_cotizacion(request):
    if request.method == "POST":
        # Aquí más adelante guardarás en la base de datos
        nuevo = {
            "id": len(COTIZACIONES) + 1,
            "cliente": request.POST.get("cliente"),
            "fecha": request.POST.get("fecha"),
            "total": request.POST.get("total"),
            "estado": request.POST.get("estado"),
        }
        COTIZACIONES.append(nuevo)
        return redirect("cotizaciones")

    # --- ESTO ES NUEVO: datos de kits y tabla de kWh ---
    kits_dict = {
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

    kwh_table = [
        {"kwh": 300, "sugerencia": "Kit On-Grid 1–2 kW"},
        {"kwh": 500, "sugerencia": "Kit On-Grid 3 kW"},
        {"kwh": 700, "sugerencia": "Kit On-Grid 4–5 kW"},
        {"kwh": 1200, "sugerencia": "Kit Off-Grid 6–10 kW"},
    ]

    context = {
        "kits_json": json.dumps(kits_dict),
        "kwh_json": json.dumps(kwh_table),
    }

    # Asegúrate que el HTML esté en templates/admin/
    return render(request, "admin/crear_cotizacion.html", context)

# Ver detalle de cotización
def ver_cotizacion(request, cot_id):
    cot = next((c for c in COTIZACIONES if c["id"] == cot_id), None)
    return render(request, "admin/ver_cotizacion.html", {"cot": cot})

# Editar cotización
def editar_cotizacion(request, cot_id):
    cot = next((c for c in COTIZACIONES if c["id"] == cot_id), None)
    if not cot:
        return HttpResponse("Cotización no encontrada.", status=404)

    if request.method == "POST":
        cot["cliente"] = request.POST.get("cliente")
        cot["fecha"] = request.POST.get("fecha")
        cot["total"] = request.POST.get("total")
        cot["estado"] = request.POST.get("estado")
        return redirect("cotizaciones")

    return render(request, "admin/editar_cotizacion.html", {"cot": cot})

# Eliminar cotización
def eliminar_cotizacion(request, cot_id):
    cot = next((c for c in COTIZACIONES if c["id"] == cot_id), None)
    if not cot:
        return HttpResponse("Cotización no encontrada.", status=404)

    if request.method == "POST":
        COTIZACIONES.remove(cot)
        return redirect("cotizaciones")

    return render(request, "admin/eliminar_cotizacion.html", {"cot": cot})
