import speech_recognition as sr
import requests
import tempfile
import os
import pyaudio
from core.config import settings
from core.logger import nervous_system
from core.tech_manager import tech_manager

# Import local STT engine
try:
    from core.engines.stt.faster_whisper_engine import FasterWhisperEngine
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    nervous_system.sensory("Faster-Whisper no disponible, usando cloud STT")

# Import VAD & Wake Word engines
try:
    from core.engines.vad.silero_engine import SileroVadEngine
    from core.engines.wakeword.porcupine_engine import PorcupineEngine
    ADVANCED_AUDIO_AVAILABLE = True
except ImportError:
    ADVANCED_AUDIO_AVAILABLE = False
    nervous_system.sensory("Módulos de audio avanzado no disponibles")

class Ear:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        
        # Auto-detect WO Mic if not configured
        if settings.MIC_DEVICE_INDEX is None:
            settings.MIC_DEVICE_INDEX = self._find_wo_mic_index()
            
        # Usar el índice configurado (o detectado)
        self.device_index = settings.MIC_DEVICE_INDEX
        
        # Auto-detect WO Mic if no index set
        if self.device_index is None:
            self.device_index = self._find_wo_mic_index()
            if self.device_index:
                settings.MIC_DEVICE_INDEX = self.device_index
        
        nervous_system.sensory(f"Inicializando micrófono (Index: {self.device_index})...")
        # 16000Hz is required for Porcupine and ideal for Silero/Whisper
        self.microphone = sr.Microphone(device_index=self.device_index, sample_rate=16000)
        
        # HuggingFace headers (fallback option)
        self.hf_headers = {
            "Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"
        } if settings.HUGGINGFACE_API_KEY else None
        
        # Initialize local STT engine (Faster-Whisper)
        self.local_engine = None
        if FASTER_WHISPER_AVAILABLE:
            try:
                self.local_engine = FasterWhisperEngine(model_size="base")
                nervous_system.sensory("✓ Faster-Whisper engine disponible")
            except Exception as e:
                nervous_system.error("SENSORY", f"Error inicializando Faster-Whisper: {e}")
        
        # Initialize Advanced Audio (VAD & Wake Word)
        self.vad_engine = None
        self.wake_word_engine = None
        
        if ADVANCED_AUDIO_AVAILABLE:
            # Check active stack configuration
            active_vad = tech_manager.get_active_engine("vad")
            active_wake = tech_manager.get_active_engine("wake_word")
            
            # Initialize VAD
            if active_vad == "silero":
                try:
                    self.vad_engine = SileroVadEngine(threshold=0.5)
                except Exception as e:
                    nervous_system.error("SENSORY", f"Error init VAD: {e}")
            
            # Initialize Wake Word
            if active_wake == "porcupine":
                try:
                    self.wake_word_engine = PorcupineEngine()
                except Exception as e:
                    nervous_system.error("SENSORY", f"Error init Porcupine: {e}")
        
        nervous_system.sensory("Nervio Auditivo (Local + Cloud) Inicializado.")

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
            # Wake Word Loop (blocking if enabled)
            # TODO: Implement full wake word loop here. 
            # For now, we assume "Always Active" or handle it in main loop if needed.
            # But let's add VAD verification post-capture.

            with self.microphone as source:
                # Wake Word Loop (blocking if enabled)
                if self.wake_word_engine:
                    nervous_system.sensory(f"Esperando palabra clave ({self.wake_word_engine.keywords})...")
                    frame_len = self.wake_word_engine.get_frame_length()
                    
                    while True:
                        # Read frame for Porcupine
                        try:
                            # Read raw bytes from PyAudio stream
                            pcm_data = source.stream.read(frame_len)
                            
                            idx = self.wake_word_engine.process(pcm_data)
                            if idx >= 0:
                                nervous_system.sensory("⚡ Wake Word detectado!")
                                # Optional: Play sound here
                                break
                        except Exception as e:
                            nervous_system.error("SENSORY", f"Error en loop Wake Word: {e}")
                            break # Fail safe to normal listening

                nervous_system.sensory("Escuchando ambiente...")
                
                # Dynamic adjustment or manual
                if self.vad_engine:
                    # If VAD is improved, we trust it more, but SR still needs energy thresh
                    # We keep standard SR behavior for capturing, then verify with Silero
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                else:
                    self.recognizer.dynamic_energy_threshold = True
                    self.recognizer.pause_threshold = 0.8
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            
            # VAD Verification (Silero)
            if self.vad_engine:
                nervous_system.sensory("Verificando voz humana (VAD)...")
                # SR AudioData to bytes
                is_speech = self.vad_engine.is_speech(audio.get_raw_data())
                if not is_speech:
                    nervous_system.sensory("VAD: Ruido detectado, ignorando.")
                    return ""
                nervous_system.sensory("VAD: Voz confirmada.")

            # Procesar transcripción
            nervous_system.sensory("Audio capturado. Procesando...")
            
            # PRIMARY: Faster-Whisper (Local, fastest, no rate limits)
            if self.local_engine is not None:
                try:
                    text = self.local_engine.transcribe(audio, language="es")
                    if text:
                        nervous_system.sensory(f"✓ Faster-Whisper (local) transcribió: {text}")
                        return text
                except Exception as e:
                    nervous_system.error("SENSORY", f"Faster-Whisper error: {e}, usando fallback...")
            
            # FALLBACK 1: Google STT (Cloud, reliable, free)
            try:
                text = self.recognizer.recognize_google(audio, language="es-ES")
                if text:
                    nervous_system.sensory(f"Google STT (fallback) escuchó: {text}")
                    return text
            except sr.UnknownValueError:
                nervous_system.sensory("Google STT no detectó habla.")
            except Exception as e:
                nervous_system.error("SENSORY", f"Google STT error: {e}")
            
            nervous_system.sensory("No se pudo transcribir el audio.")
            return ""  # No transcription found

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

            return ""

if __name__ == "__main__":
    ear = Ear()
    print(ear.listen())
