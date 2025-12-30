"""
Faster-Whisper Engine - Local Speech-to-Text
High-performance local transcription using CTranslate2-optimized Whisper
"""
import os
from faster_whisper import WhisperModel
from core.logger import nervous_system


class FasterWhisperEngine:
    """Local STT using Faster-Whisper (4x faster than standard Whisper)"""
    
    def __init__(self, model_size="base", device="cpu", compute_type="int8"):
        """
        Initialize Faster-Whisper model
        
        Args:
            model_size: "tiny", "base", "small", "medium", "large-v3"
                       base = good balance (74MB)
                       medium = better accuracy (1.5GB)
                       large-v3 = best accuracy (2.9GB)
            device: "cpu" or "cuda"
            compute_type: "int8", "int8_float16", "float16" (int8 fastest on CPU)
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None
        
        nervous_system.sensory(f"Inicializando Faster-Whisper ({model_size})...")
        
    def load_model(self):
        """Load model on first use (lazy loading)"""
        if self.model is None:
            try:
                nervous_system.sensory(f"Cargando modelo Whisper '{self.model_size}'...")
                self.model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                    download_root=os.path.join(os.path.dirname(__file__), "..", "..", "models")
                )
                nervous_system.sensory("✓ Modelo Whisper cargado exitosamente")
            except Exception as e:
                nervous_system.error("SENSORY", f"Error cargando Whisper: {e}")
                raise
    
    def transcribe(self, audio_data, language="es"):
        """
        Transcribe audio buffer to text
        
        Args:
            audio_data: SpeechRecognition AudioData object
            language: Language code (es, en, etc.)
        
        Returns:
            str: Transcribed text or None if failed
        """
        try:
            # Load model if not loaded
            if self.model is None:
                self.load_model()
            
            # Convert AudioData to raw bytes (faster-whisper needs file-like or bytes)
            import tempfile
            import wave
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                # Write WAV file
                with wave.open(temp_audio.name, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(audio_data.sample_width)
                    wf.setframerate(audio_data.sample_rate)
                    wf.writeframes(audio_data.get_raw_data())
                
                temp_path = temp_audio.name
            
            # Transcribe
            segments, info = self.model.transcribe(
                temp_path,
                language=language,
                beam_size=5,
                vad_filter=True,  # Voice Activity Detection (filters silence)
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # Combine all segments
            text = " ".join([segment.text for segment in segments]).strip()
            
            # Cleanup temp file
            try:
                os.remove(temp_path)
            except:
                pass
            
            return text if text else None
            
        except Exception as e:
            nervous_system.error("SENSORY", f"Error en transcripción Whisper: {e}")
            return None
    
    def is_available(self):
        """Check if engine is available"""
        try:
            from faster_whisper import WhisperModel
            return True
        except ImportError:
            return False


if __name__ == "__main__":
    # Test
    engine = FasterWhisperEngine(model_size="base")
    print(f"Engine available: {engine.is_available()}")
