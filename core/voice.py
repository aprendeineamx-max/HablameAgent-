import os
import asyncio
import edge_tts
import playsound
from elevenlabs import stream
from elevenlabs.client import ElevenLabs
from core.config import settings
from core.logger import nervous_system

import pyttsx3
from core.config import settings
from core.logger import nervous_system
from core.tech_manager import tech_manager

# Import Kokoro Engine
try:
    from core.engines.tts.kokoro_engine import KokoroEngine
    KOKORO_AVAILABLE = True
except ImportError:
    KOKORO_AVAILABLE = False

class Voice:
    def __init__(self):
        # Init pyttsx3 for local fallback/primary
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)
            # Select first spanish voice if available
            voices = self.engine.getProperty('voices')
            for v in voices:
                if "spanish" in v.name.lower() or "es-" in v.id.lower():
                    self.engine.setProperty('voice', v.id)
                    break
        except Exception:
            self.engine = None
            
        # Init Kokoro (Lazy load inside engine usually, but we check availability)
        self.kokoro = None
        if KOKORO_AVAILABLE:
            # We don't init immediately to avoid slow startup unless it's the active engine
            # But let's check tech_manager to see if we should
            if tech_manager.get_active_engine("tts") == "kokoro":
                self.kokoro = KokoroEngine()
            
        # Init Audio Player
        try:
             from core.player import AudioPlayer
             self.player = AudioPlayer()
        except Exception:
             self.player = None

        self.eleven = None
        # Only init ElevenLabs if explicitly active or key present AND user wants it
        if settings.ELEVENLABS_API_KEY:
            try:
                self.eleven = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
            except Exception:
                pass

    def stop(self):
        """Stop current speech immediately"""
        if self.player:
            self.player.stop()
        if self.engine:
            self.engine.stop() # pyttsx3 stop

    def speak(self, text):
        """
        Habla el texto dado usando el motor configurado en TechnologyManager.
        """
        # Stop previous before starting new
        self.stop()
        
        active_engine = tech_manager.get_active_engine("tts")
        nervous_system.vocal(f"Sintetizando voz ({active_engine}): '{text}'")
        
        try:
            if active_engine == "elevenlabs" and self.eleven:
                self._speak_elevenlabs(text)
            elif active_engine == "pyttsx3":
                self._speak_local(text)
            elif active_engine == "kokoro":
                self._speak_kokoro(text)
            elif active_engine == "edge_tts":
                asyncio.run(self._speak_edge_tts(text))
            else:
                # Fallback default
                asyncio.run(self._speak_edge_tts(text))
        except Exception as e:
            nervous_system.error("VOCAL", f"Error en TTS ({active_engine}): {e}")
            # Ultimate fallback
            if active_engine != "pyttsx3":
                self._speak_local(text)

    def _speak_local(self, text):
        """Usa pyttsx3 (100% offline)"""
        if self.engine:
            self.engine.say(text)
            self.engine.runAndWait()
        else:
            nervous_system.error("VOCAL", "Motor local pyttsx3 no inicializado")

    def _speak_kokoro(self, text):
        """Usa Kokoro TTS (Local High Quality)"""
        if not self.kokoro:
            self.kokoro = KokoroEngine()
        
        # Now returns audio data tuple (samples, sample_rate) or False
        result = self.kokoro.generate(text, return_data=True)
        
        if result:
            samples, sample_rate = result
            if self.player:
                self.player.play(samples, sample_rate)
            else:
                nervous_system.error("VOCAL", "AudioPlayer no disponible")
        else:
            raise Exception("Fallo generación Kokoro")

    def _speak_elevenlabs(self, text):
        output_file = "temp_eleven.mp3"
        try:
            # Generar audio (generador de bytes)
            audio_generator = self.eleven.text_to_speech.convert(
                text=text,
                voice_id=settings.ELEVENLABS_VOICE_ID,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128",
            )
            
            # Guardar a archivo
            with open(output_file, "wb") as f:
                for chunk in audio_generator:
                    f.write(chunk)
            
            # Reproducir
            playsound.playsound(output_file)
            
        except Exception as e:
            nervous_system.error("VOCAL", f"Fallo ElevenLabs, cambiando a fallback: {e}")
            asyncio.run(self._speak_edge_tts(text))
        finally:
            if os.path.exists(output_file):
                try:
                    os.remove(output_file)
                except: pass

    async def _speak_edge_tts(self, text):
        """Voz neuronal gratuita de Microsoft Edge (Excelente calidad local-ish)"""
        output_file = "temp_speech.mp3"
        # Voz sugerida: es-AR-TomasNeural o es-ES-AlvaroNeural para masculino, es-MX-DaliaNeural para femenino
        communicate = edge_tts.Communicate(text, "es-MX-DaliaNeural")
        await communicate.save(output_file)
        
        try:
            playsound.playsound(output_file)
        except Exception as e:
            nervous_system.error("VOCAL", f"Error reproduciendo audio: {e}")
        finally:
            if os.path.exists(output_file):
                try:
                    os.remove(output_file)
                except: pass

if __name__ == "__main__":
    voice = Voice()
    voice.speak("Prueba de sistema vocal.")
