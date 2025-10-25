# views.py — SIEER Chile (completo y ordenado)

from __future__ import annotations

from pathlib import Path
import json
import uuid
import random
from typing import Any, Dict, List

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import RegistroForm
from .models import ChatConversation, ChatMessage

# ====== Opcional: lectura de Excel (no rompe si no existe pandas/archivos) ======
try:
    import pandas as pd  # type: ignore
except Exception:
    pd = None  # fallback cuando no está instalado

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


# ============================
#          PÁGINAS BASE
# ============================

def index(request):
    return render(request, "index.html")


def productos(request):
    return render(request, "Productos.html")


def is_admin(user):
    return user.is_staff or user.is_superuser


# Registro de usuarios
def registro(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Autenticar automáticamente
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password1")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"¡Registro exitoso! Bienvenido {user.first_name}.")
                # Redirigir según tipo de usuario
                if user.is_staff or user.is_superuser:
                    return redirect("admin_panel")
                return redirect("client_dashboard")
    else:
        form = RegistroForm()
    return render(request, "registro.html", {"form": form})


# Login personalizado
class CustomLoginView(LoginView):
    template_name = "registration/login.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.user.is_staff or self.request.user.is_superuser:
            return redirect("admin_panel")
        return redirect("client_dashboard")


@login_required
@user_passes_test(is_admin)
def admin_panel(request):
    return render(request, "admin/admin_panel.html", {"user": request.user})


@login_required
def client_dashboard(request):
    return render(request, "cliente/client_dashboard.html", {"user": request.user})


# Login alternativo (si lo necesitas en alguna URL)
def custom_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_staff or user.is_superuser:
                return redirect("admin_panel")
            return redirect("client_dashboard")
        messages.error(request, "Usuario o contraseña incorrectos.")
    return render(request, "registration/login.html")


# ============================
#           CHATBOT
# ============================

def chatbot_demo(request):
    return render(request, "chatbot/chatbot_demo.html")


class FreeChatBotService:
    def __init__(self):
        self.kits_solares = {
            "ongrid": {
                "1kw": {
                    "nombre": "Kit Panel Solar 1.0 KW OnGrid",
                    "precio": "$1.500.000",
                    "ahorro_mensual": "$15.000 a $20.000",
                    "caracteristicas": [
                        "Instalado con tramitación SEC",
                        "Sistema NetBilling",
                        "Ideal para viviendas pequeñas",
                        "Pago en cuotas con cualquier tarjeta",
                    ],
                },
                "1.5kw": {
                    "nombre": "Kit Panel Solar 1.5 KW OnGrid",
                    "precio": "$1.900.000",
                    "ahorro_mensual": "$25.000 a $30.000",
                    "caracteristicas": [
                        "Instalado con tramitación SEC",
                        "Sistema NetBilling",
                        "Perfecto para familias pequeñas",
                        "Pago en cuotas con cualquier tarjeta",
                    ],
                },
                "2kw": {
                    "nombre": "Kit Panel Solar 2.0 KW OnGrid",
                    "precio": "$2.300.000",
                    "ahorro_mensual": "$28.000 a $40.000",
                    "caracteristicas": [
                        "Instalado con tramitación SEC",
                        "Sistema NetBilling",
                        "Para consumo medio residencial",
                        "Pago en cuotas con cualquier tarjeta",
                    ],
                },
                "3kw": {
                    "nombre": "Kit Panel Solar 3.0 KW OnGrid",
                    "precio": "$3.400.000",
                    "ahorro_mensual": "$40.000 a $50.000",
                    "caracteristicas": [
                        "Instalado con tramitación SEC",
                        "Sistema NetBilling",
                        "Ideal para familias medianas",
                        "Pago en cuotas con cualquier tarjeta",
                    ],
                },
                "4kw": {
                    "nombre": "Kit Panel Solar 4.0 KW OnGrid",
                    "precio": "$3.900.000",
                    "ahorro_mensual": "$60.000",
                    "caracteristicas": [
                        "Instalado con tramitación SEC",
                        "Sistema NetBilling",
                        "Para consumo alto residencial",
                        "Pago en cuotas con cualquier tarjeta",
                    ],
                },
                "5kw": {
                    "nombre": "Kit Panel Solar 5.0 KW OnGrid",
                    "precio": "$5.300.000",
                    "ahorro_mensual": "$65.000 a $85.000",
                    "caracteristicas": [
                        "Instalado con tramitación SEC",
                        "Sistema NetBilling",
                        "Para viviendas grandes",
                        "Pago en cuotas con cualquier tarjeta",
                    ],
                },
            },
            "offgrid": {
                "5kw": {
                    "nombre": "Kit OffGrid 5KW F1 Litio",
                    "precio": "$3.900.000",
                    "caracteristicas": [
                        "Autonomía nocturna de 3 a 5 horas",
                        "Instalación bajo norma SEC",
                        "2.200 watts en paneles",
                        "Respaldo en baterías 4.8KW/h",
                        "Inversor HPPT 5.200 watts",
                    ],
                },
                "6kw": {
                    "nombre": "Kit OffGrid 6KW F1 Litio",
                    "precio": "$4.220.000",
                    "caracteristicas": [
                        "Autonomía nocturna de 4 a 6 horas",
                        "Instalación bajo norma SEC",
                        "5.300 watts en paneles",
                        "Respaldo en baterías 5.2KW/h",
                        "Inversor HPPT 8.000 watts",
                    ],
                },
                "8kw": {
                    "nombre": "Kit OffGrid 8KW F1 Litio",
                    "precio": "$6.640.000",
                    "caracteristicas": [
                        "Autonomía nocturna de 6 a 8 horas",
                        "Instalación bajo norma SEC",
                        "4.400 watts en paneles",
                        "Respaldo en baterías 9.6KW/h",
                        "Inversor HPPT 8.000 watts",
                    ],
                },
                "10kw": {
                    "nombre": "Kit OffGrid 10KW F1 Litio",
                    "precio": "$7.550.000",
                    "caracteristicas": [
                        "Autonomía nocturna de 7 a 9 horas",
                        "Instalación bajo norma SEC",
                        "5.600 watts en paneles",
                        "Respaldo en baterías 9.6KW/h",
                        "Inversor HPPT 10.000 watts",
                    ],
                },
            },
        }

    def get_kit_info(self, tipo, capacidad):
        try:
            kit = self.kits_solares[tipo][capacidad]
            respuesta = f"📊 **{kit['nombre']}**\n\n"
            respuesta += f"💵 **Precio:** {kit['precio']}\n"
            if "ahorro_mensual" in kit:
                respuesta += f"💰 **Ahorro mensual:** {kit['ahorro_mensual']}\n"
            respuesta += "\n🔧 **Características:**\n"
            for c in kit["caracteristicas"]:
                respuesta += f"✅ {c}\n"
            respuesta += f"\n📞 **Contacto:** +56 9 8152 0994"
            return respuesta
        except KeyError:
            return "No tengo información de ese kit específico. ¿Podrías ser más específico?"

    def get_offgrid_general_info(self):
        return (
            "🏠 **Kits OffGrid - Energía Autónoma**\n\n"
            "Sistemas independientes de la red eléctrica. Ideales para:\n"
            "✅ Zonas sin conexión a red\n"
            "✅ Backup de energía\n"
            "✅ Propiedades rurales\n\n"
            "**Capacidades disponibles:**\n"
            "🔸 5KW - $3.900.000\n"
            "🔸 6KW - $4.220.000\n"
            "🔸 8KW - $6.640.000\n"
            "🔸 10KW - $7.550.000\n\n"
            "¿Te interesa alguna capacidad específica?"
        )

    def get_general_solar_info(self):
        return (
            "☀️ **Energía Solar en Chile**\n\n"
            "Chile tiene una de las mejores radiaciones solares del mundo 🌍\n\n"
            "**Beneficios:**\n"
            "✅ Ahorro inmediato en cuenta de luz\n"
            "✅ Retorno de inversión: 3-5 años\n"
            "✅ Energía 100% limpia y renovable\n"
            "✅ Valorización de tu propiedad\n"
            "✅ Independencia energética\n\n"
            "**Datos técnicos:**\n"
            "🔸 Vida útil paneles: 25-30 años\n"
            "🔸 Eficiencia típica: 15-22%\n"
            "🔸 Mantenimiento: Mínimo\n"
            "🔸 Garantía rendimiento: 25 años"
        )

    def get_ongrid_offgrid_comparison(self):
        return (
            "🔌 **OnGrid vs OffGrid**\n\n"
            "**Sistema OnGrid (Conectado a Red):**\n"
            "✅ Inyectas excedentes a la red\n"
            "✅ Sin baterías = menor costo\n"
            "✅ Ideal zonas urbanas con red estable\n"
            "✅ Participas en NetBilling\n\n"
            "**Sistema OffGrid (Autónomo):**\n"
            "✅ Totalmente independiente\n"
            "✅ Con baterías para uso nocturno\n"
            "✅ Perfecto zonas rurales/sin red\n"
            "✅ Backup ante cortes de luz"
        )

    def get_contact_info(self):
        return (
            "📞 **Contacto SIEER Chile**\n\n"
            "📍 **WhatsApp:** +56 9 8152 0994\n"
            "🌐 **Sitio Web:** sieer.cl\n"
            "💬 **Horario Atención:** Lunes a Viernes 9:00 - 18:00\n\n"
            "¿En qué puedo ayudarte específicamente?"
        )

    def get_greeting(self):
        return (
            "¡Hola! 👋 Soy SIEERBot, tu asistente especializado en energía solar.\n\n"
            "Puedo ayudarte con:\n"
            "🔸 Información de kits solares\n"
            "🔸 Precios y financiamiento\n"
            "🔸 Asesoría técnica\n"
            "🔸 Tramitación y legal\n\n"
            "¿En qué te puedo asistir hoy?"
        )

    def get_farewell(self):
        return (
            "¡Ha sido un gusto ayudarte! 🌞\n\n"
            "Recuerda que puedes contactarnos:\n"
            "📞 +56 9 8152 0994\n"
            "🌐 sieer.cl\n\n"
            "¡Que tengas un excelente día!"
        )

    def get_default_response(self):
        default_responses = [
            "Interesante consulta. ¿Podrías reformularla? Estoy aquí para ayudarte con kits solares, precios, instalación y más.",
            "No estoy seguro de entender. ¿Te refieres a información sobre nuestros kits solares, precios o instalación?",
            "Como asistente especializado en energía solar, puedo ayudarte con: kits disponibles, precios, financiamiento, instalación y mantenimiento. ¿Qué te interesa?",
            "¿Te gustaría saber sobre nuestros kits OnGrid u OffGrid? También puedo ayudarte con información técnica o de financiamiento.",
            "Parece que tienes una pregunta específica. ¿Podrías contarme más? Puedo ayudarte con información sobre paneles solares, inversores, baterías o instalación.",
        ]
        return random.choice(default_responses)

    def get_ai_response(self, user_message, history=None):
        msg = user_message.lower()
        # OnGrid
        if any(w in msg for w in ["1kw", "1 kw", "uno kilowatt"]):
            return self.get_kit_info("ongrid", "1kw")
        if any(w in msg for w in ["1.5kw", "1.5 kw"]):
            return self.get_kit_info("ongrid", "1.5kw")
        if any(w in msg for w in ["2kw", "2 kw"]):
            return self.get_kit_info("ongrid", "2kw")
        if any(w in msg for w in ["3kw", "3 kw"]):
            return self.get_kit_info("ongrid", "3kw")
        if any(w in msg for w in ["4kw", "4 kw"]):
            return self.get_kit_info("ongrid", "4kw")
        if any(w in msg for w in ["5kw", "5 kw"]) and "offgrid" not in msg:
            return self.get_kit_info("ongrid", "5kw")
        # OffGrid
        if any(w in msg for w in ["offgrid", "off grid", "autónomo"]):
            if "5kw" in msg:
                return self.get_kit_info("offgrid", "5kw")
            if "6kw" in msg:
                return self.get_kit_info("offgrid", "6kw")
            if "8kw" in msg:
                return self.get_kit_info("offgrid", "8kw")
            if "10kw" in msg:
                return self.get_kit_info("offgrid", "10kw")
            return self.get_offgrid_general_info()
        # Info general
        if any(w in msg for w in ["panel solar", "paneles solares", "energía solar"]):
            return self.get_general_solar_info()
        # Comparación
        if any(w in msg for w in ["ongrid vs offgrid", "diferencia", "cuál elegir"]):
            return self.get_ongrid_offgrid_comparison()
        # Contacto
        if any(w in msg for w in ["contacto", "teléfono", "whatsapp", "ubicación"]):
            return self.get_contact_info()
        # Saludos / despedidas
        if any(w in msg for w in ["hola", "buenas", "saludos"]):
            return self.get_greeting()
        if any(w in msg for w in ["adiós", "chao", "gracias", "hasta luego"]):
            return self.get_farewell()
        # Por defecto
        return self.get_default_response()


@csrf_exempt
@require_POST
def send_message(request):
    try:
        data = json.loads(request.body)
        user_message = data.get("message", "")
        session_id = data.get("session_id", "") or str(uuid.uuid4())

        bot = FreeChatBotService()
        bot_response = bot.get_ai_response(user_message)

        return JsonResponse({"status": "success", "response": bot_response, "session_id": session_id})
    except Exception as e:
        return JsonResponse(
            {"status": "error", "response": "Lo siento, ocurrió un error. Por favor intenta nuevamente.", "error": str(e)}
        )


def get_conversation_history(request, session_id):
    try:
        conversation = ChatConversation.objects.get(session_id=session_id)
        msgs = ChatMessage.objects.filter(conversation=conversation)
        history = [{"message": m.message, "is_bot": m.is_bot, "timestamp": m.timestamp.isoformat()} for m in msgs]
        return JsonResponse({"history": history})
    except ChatConversation.DoesNotExist:
        return JsonResponse({"history": []})


# ============================
#          COTIZACIONES
# ============================

# Datos en memoria (reemplazables por modelos más adelante)
COTIZACIONES: List[Dict[str, Any]] = [
    {"id": 1, "cliente": "Juan Pérez", "fecha": "2025-10-20", "total": 250000, "estado": "Pendiente"},
    {"id": 2, "cliente": "Empresa SolarTech", "fecha": "2025-10-21", "total": 480000, "estado": "Aprobada"},
]


# ------ Utilidades para Excel (opcionales) ------
def _read_df(path: Path, **kwargs):
    if not pd or not path.exists():
        return None
    try:
        return pd.read_excel(path, **kwargs)
    except Exception:
        return None


def _load_kits() -> Dict[str, List[Dict[str, Any]]]:
    """Lee kits ongrid/offgrid desde /data/*.xlsx. Si no hay archivos, devuelve {}."""
    ongrid_df = _read_df(DATA_DIR / "kits_ongrid.xlsx")
    offgrid_df = _read_df(DATA_DIR / "offgrid.xlsx")

    def normalize(df):
        if df is None or df.empty:
            return []
        cols = {c.lower().strip(): c for c in df.columns}
        name_col = cols.get("nombre") or cols.get("kit") or list(df.columns)[0]
        price_col = cols.get("precio") or cols.get("valor") or cols.get("price") or list(df.columns)[1]
        power_col = cols.get("potencia") or cols.get("kw") or cols.get("capacidad")
        items = []
        for i, row in df.iterrows():
            items.append(
                {
                    "id": int(i + 1),
                    "nombre": str(row.get(name_col, f"Kit {i+1}")),
                    "precio": float(row.get(price_col, 0) or 0),
                    "potencia": float(row.get(power_col, 0) or 0),
                }
            )
        return items

    data = {}
    if ongrid_df is not None:
        data["ongrid"] = normalize(ongrid_df)
    if offgrid_df is not None:
        data["offgrid"] = normalize(offgrid_df)
    return data


def _load_kwh_table() -> List[Dict[str, Any]]:
    """Tabla (kWh -> sugerencia). Si no existe archivo, retorna []."""
    df = _read_df(DATA_DIR / "kwh.xlsx")
    if df is None or df.empty:
        return []
    cols = {c.lower().strip(): c for c in df.columns}
    kwh_col = cols.get("kwh") or cols.get("kwh_mensual") or list(df.columns)[0]
    sug_col = cols.get("kit_sugerido") or cols.get("potencia_sugerida") or list(df.columns)[1]
    out = []
    for _, r in df.iterrows():
        out.append({"kwh": float(r.get(kwh_col, 0) or 0), "sugerencia": str(r.get(sug_col, ""))})
    return sorted(out, key=lambda x: x["kwh"])


# ------ Vistas ------
def cotizaciones_view(request):
    return render(request, "admin/cotizaciones.html", {"cotizaciones": COTIZACIONES})


def crear_cotizacion(request):
    """
    Compatible con tu formulario actual (cliente, fecha, total, estado) y,
    si agregas campos avanzados (tipo_sistema, consumo_kwh, kit_id, precio_unit, cantidad, descuento, iva),
    también los procesa y calcula total cuando viene en hidden.
    """
    # Datos para el formulario avanzado (no rompe si faltan archivos):
    kits = _load_kits()
    kwh_table = _load_kwh_table()

    if request.method == "POST":
        # Campos básicos
        cliente = request.POST.get("cliente")
        fecha = request.POST.get("fecha")
        estado = request.POST.get("estado")

        # Si tu formulario avanzado envía 'total' calculado (hidden), úsalo.
        total = request.POST.get("total")
        if total is None:
            # Compatibilidad con la versión simple que envía "total" visible
            total = request.POST.get("total", "0")

        # Extras (opcionales)
        tipo_sistema = request.POST.get("tipo_sistema")           # ongrid / offgrid
        consumo_kwh = request.POST.get("consumo_kwh")
        kit_id = request.POST.get("kit_id")
        precio_unit = request.POST.get("precio_unit")
        cantidad = request.POST.get("cantidad")
        descuento = request.POST.get("descuento")
        iva = request.POST.get("iva")

        nuevo = {
            "id": (COTIZACIONES[-1]["id"] + 1) if COTIZACIONES else 1,
            "cliente": cliente,
            "fecha": fecha,
            "total": float(total or 0),
            "estado": estado,
            # guardamos también los opcionales si existen:
            "tipo_sistema": tipo_sistema,
            "consumo_kwh": consumo_kwh,
            "kit_id": kit_id,
            "precio_unit": precio_unit,
            "cantidad": cantidad,
            "descuento": descuento,
            "iva": iva,
        }
        COTIZACIONES.append(nuevo)
        return redirect("cotizaciones")

    context = {
        "kits_json": json.dumps(kits),         # {} si no hay Excel
        "kwh_json": json.dumps(kwh_table),     # [] si no hay Excel
    }
    return render(request, "admin/crear_cotizacion.html", context)


def ver_cotizacion(request, cot_id: int):
    cot = next((c for c in COTIZACIONES if c["id"] == cot_id), None)
    if not cot:
        return HttpResponse("Cotización no encontrada.", status=404)
    return render(request, "admin/ver_cotizacion.html", {"cot": cot})


def editar_cotizacion(request, cot_id: int):
    cot = next((c for c in COTIZACIONES if c["id"] == cot_id), None)
    if not cot:
        return HttpResponse("Cotización no encontrada.", status=404)

    if request.method == "POST":
        cot["cliente"] = request.POST.get("cliente")
        cot["fecha"] = request.POST.get("fecha")
        cot["total"] = float(request.POST.get("total", cot.get("total", 0)))
        cot["estado"] = request.POST.get("estado")
        return redirect("cotizaciones")

    return render(request, "admin/editar_cotizacion.html", {"cot": cot})


def eliminar_cotizacion(request, cot_id: int):
    cot = next((c for c in COTIZACIONES if c["id"] == cot_id), None)
    if not cot:
        return HttpResponse("Cotización no encontrada.", status=404)

    if request.method == "POST":
        COTIZACIONES.remove(cot)
        return redirect("cotizaciones")

    return render(request, "admin/eliminar_cotizacion.html", {"cot": cot})
