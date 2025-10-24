import os
import openai
from django.conf import settings
import json

class ChatBotService:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        openai.api_key = self.api_key

    def get_ai_response(self, user_message, conversation_history=None):
        """
        Obtiene respuesta de IA basada en el mensaje del usuario
        """
        try:
            # Contexto del sistema para el chatbot
            system_prompt = """
            Eres SIEERBot, el asistente virtual de SIEER Chile, especialista en servicios de ingeniería eléctrica y energía solar.

            Información de la empresa:
            - Nombre: SIEER Chile
            - Servicios: Instalaciones eléctricas, energía solar, mantenimiento
            - Productos: Kits solares On-Grid y Off-Grid desde 1KW hasta 10KW
            - Contacto: +56 9 8152 0994
            - Website: sieer.cl

            Tu rol:
            1. Responder preguntas sobre servicios eléctricos y energía solar
            2. Asesorar sobre kits solares apropiados según necesidades
            3. Explicar conceptos técnicos de manera simple
            4. Derivar a contacto humano cuando sea necesario
            5. Ser amable, profesional y útil

            Responde siempre en español.
            """

            messages = [
                {"role": "system", "content": system_prompt}
            ]

            # Agregar historial de conversación si existe
            if conversation_history:
                for msg in conversation_history:
                    role = "assistant" if msg['is_bot'] else "user"
                    messages.append({"role": role, "content": msg['message']})

            # Agregar el mensaje actual del usuario
            messages.append({"role": "user", "content": user_message})

            # Llamar a la API de OpenAI
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            return f"Lo siento, estoy teniendo dificultades técnicas. Por favor contacta al +56 9 8152 0994 para asistencia inmediata. Error: {str(e)}"

# Servicio alternativo gratis (usando modelo libre)
class FreeChatBotService:
    def get_ai_response(self, user_message):
        """
        Servicio gratuito usando Hugging Face (opcional)
        """
        import requests
        
        # API de Hugging Face (gratis)
        API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
        headers = {"Authorization": "Bearer tu_token_hugging_face"}
        
        try:
            response = requests.post(API_URL, headers=headers, json={
                "inputs": user_message,
            })
            result = response.json()
            return result.get('generated_text', 'Lo siento, no pude procesar tu mensaje.')
        except:
            return "¡Hola! Soy SIEERBot. ¿En qué puedo ayudarte con servicios eléctricos o energía solar?"