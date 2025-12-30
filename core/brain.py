from openai import OpenAI
import json
from core.config import settings
from core.logger import nervous_system

# Import local LLM engine
try:
    from core.engines.llm.ollama_engine import OllamaEngine
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    nervous_system.cognitive("Ollama no disponible, usando cloud LLM")

class Brain:
    def __init__(self):
        # LOCAL LLM (Primary - if available)
        self.local_llm = None
        if OLLAMA_AVAILABLE:
            try:
                self.local_llm = OllamaEngine(model="llama3.1:8b")
                if self.local_llm.is_available():
                    nervous_system.cognitive("✓ Ollama LLaMA (local) disponible")
                else:
                    self.local_llm = None
            except Exception as e:
                nervous_system.error("COGNITIVE", f"Error inicializando Ollama: {e}")
        
        # CLOUD LLM (Fallback - SambaNova)
        # SambaNova es compatible con la librería de OpenAI si cambiamos la URL base
        self.client = OpenAI(
            base_url=settings.SAMBANOVA_URL,
            api_key=settings.SAMBANOVA_API_KEY
        )
        # Using Llama 3.3 70B - current SambaNova model (405B is deprecated)
        self.model = "Meta-Llama-3.3-70B-Instruct" 
        nervous_system.cognitive(f"Cortex Central (Local+Cloud) Conectado.")

    def think(self, user_message):
        nervous_system.cognitive(f"Analizando intención: '{user_message}'...")
        
        # PRIMARY: Ollama (Local LLM - no rate limits)
        if self.local_llm is not None:
            try:
                response = self.local_llm.think(user_message, self._get_system_prompt())
                if response:
                    nervous_system.cognitive(f"✓ Ollama (local): {response[:100]}...")
                    return json.loads(response)
            except json.JSONDecodeError as e:
                nervous_system.error("COGNITIVE", f"Ollama JSON inválido: {e}")
            except Exception as e:
                nervous_system.error("COGNITIVE", f"Ollama error: {e}, usando fallback...")
        
        # FALLBACK: SambaNova (Cloud LLM)
        try:
            nervous_system.cognitive("Usando SambaNova (cloud fallback)...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
                max_tokens=512
            )
            
            content = response.choices[0].message.content
            nervous_system.cognitive(f"Sinapsis completada (SambaNova). Plan: {content[:100]}...")
            return json.loads(content)
            
        except Exception as e:
            nervous_system.error("COGNITIVE", f"Derrame cerebral (Error API): {e}")
            return {"action": "error", "parameters": {}}
    
    def _get_system_prompt(self):
        """
        Returns the system prompt for the LLM.
        """
        return """
        Eres un Asistente de Accesibilidad para Windows (PC Agent).
        Tu objetivo es permitir que el usuario controle TODO el ordenador con voz.
        
        Responde SIEMPRE en formato JSON estricto con la siguiente estructura:
        {
            "thought": "Breve razonamiento de qué hacer",
            "action": "nombre_de_accion",
            "parameters": { ... }
        }

        ACCIONES DISPONIBLES:
        
        BÁSICAS:
        1. "open_app": {"app_name": "nombre_o_ruta"} -> Abrir programas, carpetas o archivos (Ej: "notepad", "C:/Users")
        2. "type": {"text": "texto"} -> Escribir texto
        3. "press_key": {"key": "tecla"} -> Presionar tecla o combinación (enter, ctrl+c)
        4. "click": {"element": "nombre"} -> Clic en botones/menús (tiene fallback inteligente)
        5. "create_file": {"path": "ruta", "content": "texto"} -> Crear archivo de texto (OS level)
        
        COMANDOS DIRECTOS (Más rápidos y confiables):
        6. "save": {} -> Guardar documento actual (Ctrl+S)
        7. "minimize": {} -> Minimizar ventana activa
        8. "maximize": {} -> Maximizar ventana activa
        9. "close_window": {} -> Cerrar ventana activa
        10. "refresh": {} -> Actualizar/Recargar (F5)
        11. "screenshot": {} -> Tomar captura de pantalla
        12. "switch_app": {} -> Cambiar entre aplicaciones
        
        ESPECIALES:
        SPECIALS:
        12. "chain": {"steps": [{"action": "...", "parameters": ...}, ...]} -> Multi-step sequence
        13. "unknown": {} -> If command is unintelligible
        14. "chat": {"text": "Respuesta conversacional..."} -> PARLOTE/AMIGO. Úsalo para responder preguntas, saludar o conversar.
        15. "clarify": {"question": "¿Qué archivo quieres?"} -> PREGUNTA. Úsalo si la orden es ambigua y necesitas más info.

        MODOS DE OPERACIÓN (Adáptate según el contexto):
        - Si el usuario SALUDA o PREGUNTA algo general ("¿Cómo estás?", "¿Qué es AI?"): USA "chat".
        - Si el usuario ORDENA ("Abre esto", "Escribe aquello"): USA "open_app", "type", etc.
        - Si la orden es CLARA pero compleja: USA "chain".
        - Si la orden es AMBIGUA ("Abre el archivo"): USA "clarify".

        IMPORTANTE: 
        - Si el usuario pide crear un archivo, PREFIERE "create_file" (es más seguro que abrir notepad).
        - Si el usuario pide varias cosas ("abre esto y escribe aquello"), USA "chain".
        
        Ejemplo Chain:
        User: "Abre notepad y escribe hola"
        {
            "thought": "Usuario pide secuencia",
            "action": "chain",
            "parameters": {
                "steps": [
                    {"action": "open_app", "parameters": {"app_name": "notepad"}},
                    {"action": "type", "parameters": {"text": "hola"}}
                ]
            }
        }

        Ejemplo Chat:
        User: "Hola amigo"
        { "thought": "Saludo social", "action": "chat", "parameters": { "text": "¡Hola! ¿En qué te ayudo hoy?" } }

        Ejemplo Clarify:
        User: "Abre el documento"
        { "thought": "Ambiguo, hay muchos docs", "action": "clarify", "parameters": { "question": "¿Cual documento necesitas? ¿El de reporte o notas?" } }


        Ejemplo 1 - Comando directo:
        User: "guarda el documento"
        {
            "thought": "Usuario quiere guardar, uso comando directo",
            "action": "save",
            "parameters": {}
        }

        Ejemplo 2 - Secuencia:
        User: "Abre el bloc de notas y escribe hola"
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
