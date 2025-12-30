import speech_recognition as sr
import os
import requests
import tempfile
from core.config import settings
from core.logger import nervous_system

class Ear:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        
        # Auto-detect WO Mic if not configured
        if settings.MIC_DEVICE_INDEX is None:
            settings.MIC_DEVICE_INDEX = self._find_wo_mic_index()
            
        # Usar el índice configurado (o detectado)
        self.device_index = settings.MIC_DEVICE_INDEX
        self.microphone = sr.Microphone(device_index=self.device_index)
        
        nervous_system.sensory(f"Inicializando micrófono (Index: {self.device_index})...")
        self.hf_headers = {
            "Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"
        }
        nervous_system.sensory("Nervio Auditivo (HuggingFace) Inicializado.")

    @staticmethod
    def _find_wo_mic_index():
        """
        Busca automáticamente el dispositivo WO Mic.
        CRITICAL: WO Mic Wave (index 18) fails with PyAudio error -9999
        We need to use the regular "WO Mic Device" instead
        """
        mics = Ear.list_microphones()
        wo_mic_candidates = []
        
        for i, mic_name in enumerate(mics):
            if "wo mic" in mic_name.lower():
                nervous_system.sensory(f"Candidato WO Mic encontrado: [{i}] {mic_name}")
                wo_mic_candidates.append((i, mic_name))
        
        if not wo_mic_candidates:
            nervous_system.error("SENSORY", "No se encontró ningún dispositivo WO Mic")
            return None
        
        # AVOID "Wave" variant - it causes -9999 error
        # Prefer "WO Mic Device" (indices 1, 6, 12)
        for idx, name in wo_mic_candidates:
            if "wave" not in name.lower() and "device" in name.lower():
                nervous_system.sensory(f"Seleccionado WO Mic (Device) en índice {idx}")
                return idx
        
        # If no "Device" found, try first non-Wave option
        for idx, name in wo_mic_candidates:
            if "wave" not in name.lower():
                nervous_system.sensory(f"Seleccionado WO Mic en índice {idx}")
                return idx
        
        # Last resort: use first candidate (but warn)
        idx, name = wo_mic_candidates[0]
        nervous_system.error("SENSORY", f"WARNING: Using {name} at {idx} - may not work")
        return idx

    @staticmethod
    def list_microphones():
        """Retorna una lista de nombres de micrófonos disponibles."""
        try:
            return sr.Microphone.list_microphone_names()
        except Exception:
            return []

    def set_device_index(self, index: int):
        """Cambia el micrófono activo."""
        try:
            nervous_system.sensory(f"Cambiando micrófono a índice {index}...")
            self.device_index = index
            self.microphone = sr.Microphone(device_index=index)
            settings.MIC_DEVICE_INDEX = index # Actualizar settings en memoria
            return True
        except Exception as e:
            nervous_system.error("SENSORY", f"Error al cambiar micrófono: {e}")
            return False

    def listen(self, timeout=5, phrase_time_limit=10):
        try:
            with self.microphone as source:
                nervous_system.sensory("Escuchando ambiente...")
                # Ajuste manual calibrado
                self.recognizer.dynamic_energy_threshold = True  # Re-habilitar ajuste dinamico
                # self.recognizer.energy_threshold = 1000  # Dejar que el dinámico decida o iniciar en 300
                self.recognizer.pause_threshold = 0.8    # Un poco mas de espera para pausas naturales
                
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            
            nervous_system.sensory("Audio capturado. Enviando a la nube...")
            return self._transcribe_hf(audio)

        except sr.WaitTimeoutError:
            return None
        except AttributeError:
            # Captura el error de PyAudio cuando falla el init del stream
            nervous_system.error("SENSORY", "Fallo al abrir Stream de Audio. Reintentando...")
            import time; time.sleep(2) # Esperar antes de reintentar para no saturar log
            return None
        except Exception as e:
            nervous_system.error("SENSORY", f"Fallo en micrófono: {e}")
            import time; time.sleep(1)
            return None

    def _transcribe_hf(self, audio_data):
        """Envía el audio a HuggingFace Inference API (Whisper Large v3)"""
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                temp_audio.write(audio_data.get_wav_data())
                temp_audio_path = temp_audio.name

            with open(temp_audio_path, "rb") as f:
                data = f.read()

            response = requests.post(
                settings.HUGGINGFACE_WHISPER_URL,
                headers=self.hf_headers,
                data=data
            )
            
            os.remove(temp_audio_path)

            if response.status_code == 200:
                result = response.json()
                text = result.get("text", "")
                nervous_system.sensory(f"Input Interpretado: '{text}'")
                return text
            else:
                nervous_system.error("SENSORY", f"Error HF ({response.status_code}): {response.text}")
                return self._transcribe_local_fallback(audio_data)

        except Exception as e:
            nervous_system.error("SENSORY", f"Excepción HF: {e}")
            return self._transcribe_local_fallback(audio_data)

    def _transcribe_local_fallback(self, audio_data):
        try:
            text = self.recognizer.recognize_google(audio_data, language="es-ES")
            nervous_system.sensory(f"Fallback (Google) escuchó: {text}")
            return text
        except:
            return ""

if __name__ == "__main__":
    ear = Ear()
    print(ear.listen())
