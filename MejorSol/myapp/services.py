
import os
import requests
from django.conf import settings
import json

# ===========================
# USAREMOS EL SERVICIO GRATUITO PARA EMPEZAR
# ===========================

class ChatBotService:
    def get_ai_response(self, user_message, conversation_history=None):
        """
        Servicio gratuito usando Hugging Face (opcional)
        """
        # API de Hugging Face (gratis)
        API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
        
        # ¡¡DEBES CONSEGUIR TU TOKEN EN HUGGINGFACE.CO!!
        # Ve a tu Perfil -> Settings -> Access Tokens -> New Token
        HF_TOKEN = os.getenv('HF_TOKEN', 'AQUI_VA_TU_TOKEN_DE_HUGGING_FACE')
        
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        
        try:
            response = requests.post(API_URL, headers=headers, json={
                "inputs": user_message,
            })
            result = response.json()
            # Manejo de error si el modelo está cargando
            if "error" in result and "is currently loading" in result["error"]:
                return "El modelo de IA está cargando. Por favor, inténtalo de nuevo en unos segundos."
            
            return result.get('generated_text', 'Lo siento, no pude procesar tu mensaje.')
        except Exception as e:
            print(f"Error en FreeChatBotService: {e}")
            return "¡Hola! Soy SIEERBot. ¿En qué puedo ayudarte con servicios eléctricos o energía solar?"