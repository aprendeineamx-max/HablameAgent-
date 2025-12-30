"""
Ollama LLaMA Engine - Local Language Model
High-performance local LLM using Ollama
"""
import json
import ollama
from core.logger import nervous_system


class OllamaEngine:
    """Local LLM using Ollama (LLaMA 3.1)"""
    
    def __init__(self, model="llama3.2:1b"):
        self.host = "http://localhost:11434"
        self.model = model
        self.max_retries = 2
        
        try:
            nervous_system.cognitive(f"Inicializando Ollama ({self.model})...")
        except Exception as e:
            print(f"Error log: {e}")
        
        # Check if Ollama is running
        if not self.is_available():
            nervous_system.error("COGNITIVE", "Ollama no está ejecutándose. Inicia Ollama Desktop.")
    
    def think(self, user_message, system_prompt):
        """
        Generate response from LLM
        
        Args:
            user_message: User's command/query
            system_prompt: System instructions
        
        Returns:
            str: JSON response or None if failed
        """
        try:
            nervous_system.cognitive(f"Pensando con Ollama ({self.model})...")
            
            # Call Ollama
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                options={
                    "temperature": 0.3,  # Lower = more focused
                    "num_predict": 256,  # Max tokens
                }
            )
            
            # Extract response
            content = response['message']['content']
            
            # Try to parse JSON (Ollama sometimes wraps in markdown)
            if "```json" in content:
                # Extract JSON from markdown code block
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            elif "```" in content:
                # Generic code block
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            
            # Validate JSON
            try:
                json.loads(content)
                return content
            except json.JSONDecodeError:
                nervous_system.error("COGNITIVE", f"Respuesta no es JSON válido: {content}")
                # Try to extract JSON object
                if "{" in content and "}" in content:
                    start = content.find("{")
                    end = content.rfind("}") + 1
                    extracted = content[start:end]
                    json.loads(extracted)  # Validate
                    return extracted
                return None
            
        except ollama.ResponseError as e:
            nervous_system.error("COGNITIVE", f"Error Ollama API: {e}")
            return None
        except Exception as e:
            nervous_system.error("COGNITIVE", f"Error en Ollama: {e}")
            return None
    
    def is_available(self):
        """Check if Ollama is running and model is available"""
        try:
            # Try to list models
            response = ollama.list()
            
            # Response is an object with .models attribute
            if hasattr(response, 'models'):
                models = response.models
                model_names = [m.model for m in models if hasattr(m, 'model')]
            else:
                nervous_system.error("COGNITIVE", f"Formato inesperado de ollama.list(): {response}")
                return False
            
            # Check if our model is available (exact match or base name match)
            if self.model in model_names:
                return True
            
            # Check base name (e.g., "llama3.1" from "llama3.1:8b")
            base_model = self.model.split(':')[0]
            for name in model_names:
                if name.startswith(base_model):
                    return True
            
            nervous_system.error("COGNITIVE", f"Modelo '{self.model}' no encontrado. Ejecuta: ollama pull {self.model}")
            return False
                
        except Exception as e:
            nervous_system.error("COGNITIVE", f"Ollama no disponible: {e}")
            return False


if __name__ == "__main__":
    # Test
    engine = OllamaEngine()
    if engine.is_available():
        print("✓ Ollama disponible")
        
        # Test simple query
        system = "You are a helpful assistant. Respond in JSON format: {\"response\": \"your answer\"}"
        user = "What is 2+2?"
        result = engine.think(user, system)
        print(f"Result: {result}")
    else:
        print("✗ Ollama no disponible")
