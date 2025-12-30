"""
Kokoro TTS Engine - High Quality Local Text-to-Speech
Uses Kokoro-ONNX for fast, offline inference
"""
import os
import soundfile as sf
from kokoro_onnx import Kokoro
import numpy as np
from core.logger import nervous_system
from core.config import settings
from core.tech_manager import tech_manager

class KokoroEngine:
    def __init__(self):
        self.kokoro = None
        self.sample_rate = 24000
        self.voice_name = "es_pe" # Spanish voice (Peruvian accent is often neutral enough, or check available)
        # es_es is better if available in the model mix
        
        try:
            nervous_system.vocal("Inicializando Kokoro TTS (Local)...")
            
            # Ensure model file exists (approx 80-100MB)
            # For simplicity in this script, we'll try to load default. 
            # In a real setup we might need to download the .onnx file first if not present.
            # kokoro-onnx library often handles some of this or expects a path.
            
            if not os.path.exists("kokoro/kokoro-v0_19.onnx") or not os.path.exists("kokoro/voices-v1.0.bin"):
                nervous_system.vocal("Descargando modelo Kokoro TTS (80MB)...")
                try:
                    import requests
                    if not os.path.exists("kokoro"):
                        os.makedirs("kokoro")
                    
                    # URLs for Kokoro v0.19 ONNX from known GitHub release
                    model_url = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0_19.onnx"
                    voices_url = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
                    
                    # Download Model
                    if not os.path.exists("kokoro/kokoro-v0_19.onnx"):
                        r = requests.get(model_url, allow_redirects=True)
                        with open("kokoro/kokoro-v0_19.onnx", 'wb') as f:
                            f.write(r.content)
                        
                    # Download Voices
                    r = requests.get(voices_url, allow_redirects=True)
                    with open("kokoro/voices-v1.0.bin", 'wb') as f:
                        f.write(r.content)

                    nervous_system.vocal("✓ Modelo Kokoro descargado")
                except Exception as e:
                    nervous_system.error("VOCAL", f"Error descargando Kokoro: {e}")
                    return

            self.kokoro = Kokoro("kokoro/kokoro-v0_19.onnx", "kokoro/voices-v1.0.bin")
            
            # Load active voice from settings/tech_manager if available, else default
            active_voice = tech_manager.get_engine_option("tts", "kokoro", "voice")
            
            # Verify if this voice actually exists in the loaded model
            available = self.get_available_voices()
            if active_voice not in available and available:
                nervous_system.vocal(f"Voz configurada '{active_voice}' no encontrada. Usando primera disponible: {available[0]}")
                self.voice_name = available[0]
            else:
                self.voice_name = active_voice if active_voice else "af_bella" # Default to a safe known voice
            
            nervous_system.vocal(f"✓ Kokoro TTS cargado (Voz: {self.voice_name})")
            
        except Exception as e:
            nervous_system.error("VOCAL", f"Error Kokoro: {e}")

    def get_available_voices(self):
        """Return list of available voices from loaded kokoro instance or file"""
        try:
            # If kokoro is loaded, it might have a get_voices() or we can inspect the voices.bin manually?
            # The python lib 'kokoro_onnx' usually has 'get_voices()'
            if self.kokoro and hasattr(self.kokoro, "get_voices"):
                 return self.kokoro.get_voices()
            
            # Fallback hardcoded list of v1.0 voices to avoid crashes if we can't read it
            return [
                "af_bella", "af_sarah", "am_adam", "am_michael",
                "bf_emma", "bf_isabella", "bm_george", "bm_lewis",
                "es_pe", "es_es", "fr_fr", "hi_hi", "it_it", "pt_br"
            ]
        except Exception as e:
            nervous_system.error("VOCAL", f"Error listing voices: {e}")
            return ["af_bella"]

    def set_voice(self, voice_name):
        """Change the active voice"""
        if voice_name in self.get_available_voices():
            self.voice_name = voice_name
            # Update config persistent
            tech_manager.set_engine_option("tts", "kokoro", "voice", voice_name)
            nervous_system.vocal(f"Voz Kokoro cambiada a: {voice_name}")
            return True
        return False

    def generate(self, text, output_file=None, return_data=False):
        """Generate audio file from text or return data"""
        if not self.kokoro:
            # Attempt lazy load or fail
            return False
            
        try:
            # Determine lang from voice name (simple heuristic)
            lang = "es" if "es" in self.voice_name else "en-us"
            if "bf" in self.voice_name or "bm" in self.voice_name:
                lang = "en-gb"
            
            # Simple language mapping for Kokoro
            if self.voice_name.startswith("es"):
                lang = "es"
            elif self.voice_name.startswith("af") or self.voice_name.startswith("am"):
                lang = "en-us"
            elif self.voice_name.startswith("bf") or self.voice_name.startswith("bm"):
                lang = "en-gb"
            
            samples, sample_rate = self.kokoro.create(
                text, voice=self.voice_name, speed=1.0, lang=lang
            )
            
            if output_file:
                sf.write(output_file, samples, sample_rate)
                
            if return_data:
                return samples, sample_rate
            
            return True
        except Exception as e:
            nervous_system.error("VOCAL", f"Error generando audio Kokoro: {e}")
            return False
