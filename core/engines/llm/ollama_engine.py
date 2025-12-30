"""
Ollama LLaMA Engine - Local Language Model
High-performance local LLM using Ollama
"""
import json
import ollama
from core.logger import nervous_system


class OllamaEngine:
    """Local LLM using Ollama (LLaMA 3.1)"""
    
    def __init__(self, model="llama3.1:8b"):
        """
        Initialize Ollama engine
        
        Args:
            model: Model name (llama3.1:8b, llama3.1:70b, etc.)
        """
        self.model = model
        nervous_system.cognitive(f"Inicializando Ollama ({model})...")
        
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
            models = ollama.list()
            
            # Check if our model is available
            model_names = [m['name'] for m in models.get('models', [])]
            if self.model in model_names or self.model.split(':')[0] in [m.split(':')[0] for m in model_names]:
                return True
            else:
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
