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
        
        BÁSICAS:
        1. "open_app": {"app_name": "nombre"} -> Abrir programas (notepad, chrome, calculator)
        2. "type": {"text": "texto"} -> Escribir texto
        3. "press_key": {"key": "tecla"} -> Presionar tecla o combinación (enter, ctrl+c)
        4. "click": {"element": "nombre"} -> Clic en botones/menús (tiene fallback inteligente)
        
        COMANDOS DIRECTOS (Más rápidos y confiables):
        5. "save": {} -> Guardar documento actual (Ctrl+S)
        6. "minimize": {} -> Minimizar ventana activa
        7. "maximize": {} -> Maximizar ventana activa
        8. "close_window": {} -> Cerrar ventana activa
        9. "refresh": {} -> Actualizar/Recargar (F5)
        10. "screenshot": {} -> Tomar captura de pantalla
        11. "switch_app": {} -> Cambiar entre aplicaciones
        
        ESPECIALES:
        12. "chain": {"steps": [...]} -> Ejecutar múltiples acciones en secuencia
        13. "unknown": {} -> Si no entiendes el comando

        IMPORTANTE: Prefiere comandos directos cuando sea posible. Por ejemplo:
        - "guarda esto" -> usa "save" en vez de click en "Guardar"
        - "minimiza" -> usa "minimize" en vez de click en botón minimizar
        - "cierra" -> usa "close_window" en vez de click en X

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
