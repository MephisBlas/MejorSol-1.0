import os
import requests
from google.cloud import dialogflow_v2 as dialogflow


# =====================================================
#   CHATBOT GRATUITO (HUGGINGFACE)
# =====================================================

class ChatBotService:
    """
    Servicio opcional que usa HuggingFace (DialoGPT-medium).
    No interfiere con el chatbot de Dialogflow.
    """

    API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"

    def get_ai_response(self, user_message):
        HF_TOKEN = os.getenv('HF_TOKEN', 'AQUI_VA_TU_TOKEN_DE_HUGGING_FACE')

        headers = {"Authorization": f"Bearer {HF_TOKEN}"}

        try:
            response = requests.post(self.API_URL, headers=headers, json={
                "inputs": user_message,
            })

            result = response.json()

            # Modelo está cargando
            if "error" in result and "is currently loading" in result["error"]:
                return "El modelo de IA está cargando. Inténtalo nuevamente."

            return result.get("generated_text", "No pude procesar tu mensaje.")

        except Exception as e:
            print(f"Error en ChatBotService: {e}")
            return "¡Hola! Soy SIEERBot. ¿En qué puedo ayudarte?"


# ==========================================================
#                  SERVICIO OFICIAL DIALOGFLOW
# ==========================================================

class DialogflowService:
    """
    Servicio para comunicar Django ↔ Dialogflow ES/CX.
    """

    def __init__(self):
        self.project_id = os.getenv("DIALOGFLOW_PROJECT_ID")
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

        # VALIDACIONES
        if not self.project_id:
            raise Exception("❌ Falta DIALOGFLOW_PROJECT_ID en variables de entorno.")

        if not credentials_path:
            raise Exception("❌ Falta GOOGLE_APPLICATION_CREDENTIALS en variables de entorno.")

        if not os.path.exists(credentials_path):
            raise Exception(f"❌ Archivo JSON no encontrado: {credentials_path}")

        # Google se autentica automáticamente con GOOGLE_APPLICATION_CREDENTIALS
        self.session_client = dialogflow.SessionsClient()

    def detect_intent(self, session_id, text, language_code="es"):
        """
        Envía texto a Dialogflow y retorna respuesta estructurada.
        """

        session = self.session_client.session_path(self.project_id, session_id)

        text_input = dialogflow.TextInput(text=text, language_code=language_code)
        query_input = dialogflow.QueryInput(text=text_input)

        try:
            response = self.session_client.detect_intent(
                request={
                    "session": session,
                    "query_input": query_input
                }
            )

            result = response.query_result

            return {
                "query": result.query_text,
                "response": result.fulfillment_text,
                "intent": result.intent.display_name,
                "confidence": result.intent_detection_confidence,
            }

        except Exception as e:
            print(f"Error en DialogflowService: {e}")
            return {
                "error": "Error al comunicar con Dialogflow",
                "detail": str(e)
            }