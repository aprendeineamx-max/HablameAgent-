import os
import asyncio
import edge_tts
import playsound
from elevenlabs import stream
from elevenlabs.client import ElevenLabs
from core.config import settings
from core.logger import nervous_system

class Voice:
    def __init__(self):
        self.eleven = None
        if settings.ELEVENLABS_API_KEY:
            try:
                self.eleven = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
                nervous_system.vocal("Cuerdas Vocales (ElevenLabs) Listas.")
            except Exception as e:
                nervous_system.error("VOCAL", f"Error ElevenLabs: {e}")

    def speak(self, text):
        """
        Habla el texto dado. Detecta automáticamente si usar ElevenLabs (Cloud) o EdgeTTS (Local).
        """
        nervous_system.vocal(f"Sintetizando voz: '{text}'")
        
        if settings.is_cloud_mode and self.eleven and settings.ELEVENLABS_VOICE_ID:
            self._speak_elevenlabs(text)
        else:
            # Necesitamos un loop para correr la función async de edge-tts
            asyncio.run(self._speak_edge_tts(text))

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
