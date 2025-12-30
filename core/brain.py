from openai import OpenAI
import json
from core.config import settings
from core.logger import nervous_system

class Brain:
    def __init__(self):
        # SambaNova es compatible con la librería de OpenAI si cambiamos la URL base
        self.client = OpenAI(
            base_url=settings.SAMBANOVA_URL,
            api_key=settings.SAMBANOVA_API_KEY
        )
        # Using Llama 3.3 70B - current SambaNova model (405B is deprecated)
        self.model = "Meta-Llama-3.3-70B-Instruct" 
        nervous_system.cognitive(f"Cortex Central (SambaNova {self.model}) Conectado.")

    def think(self, user_input, screen_context=None):
        """
        Analiza el input del usuario y retorna una ACCIÓN estructurada (JSON).
        """
        nervous_system.cognitive(f"Analizando intención: '{user_input}'...")
        
        system_prompt = """
        Eres un Asistente de Accesibilidad para Windows (PC Agent).
        Tu objetivo es permitir que el usuario controle TODO el ordenador con voz.
        
        Responde SIEMPRE en formato JSON estricto con la siguiente estructura:
        {
            "thought": "Breve razonamiento de qué hacer",
            "action": "nombre_de_accion",
            "parameters": { ... }
        }

        ACCIONES DISPONIBLES:
        1. "open_app": {"app_name": "nombre"} -> Abrir programas
        2. "type": {"text": "texto"} -> Escribir texto
        3. "press_key": {"key": "nombre_tecla"} -> Presionar una tecla (enter, tab, esc)
        4. "click": {"element": "descripción visual del elemento"} -> Hacer clic en botones/iconos
        5. "system": {"command": "volume_up/mute/shutdown"} -> Control sistema
        6. "unknown": {} -> Si no entiendes

        Ejemplo User: "Abre el bloc de notas y escribe hola"
        Ejemplo Response:
        {
            "thought": "Usuario quiere abrir notepad y escribir",
            "action": "chain", 
            "parameters": {
                "steps": [
                    {"action": "open_app", "parameters": {"app_name": "notepad"}},
                    {"action": "type", "parameters": {"text": "hola"}}
                ]
            }
        }
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Comando: {user_input}"}
                ],
                temperature=0.1,  # Determinista para acciones
                response_format={"type": "json_object"} # Forzar JSON
            )
            
            content = response.choices[0].message.content
            nervous_system.cognitive(f"Sinapsis completada. Plan: {content[:100]}...") # Log resumido
            return json.loads(content)

        except Exception as e:
            nervous_system.error("COGNITIVE", f"Derrame cerebral (Error API): {e}")
            return {"action": "error", "error": str(e)}

if __name__ == "__main__":
    brain = Brain()
    res = brain.think("Abre Google Chrome por favor")
    # print(res)
