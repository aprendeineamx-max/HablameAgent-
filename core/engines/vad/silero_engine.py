"""
Silero VAD Engine - Local Voice Activity Detection
Uses pre-trained neural network to detect speech vs noise
"""
import torch
import numpy as np
import os
from core.logger import nervous_system

class SileroVadEngine:
    def __init__(self, threshold=0.5):
        """
        Initialize Silero VAD
        Args:
            threshold: Probability threshold for speech (0.0 - 1.0)
        """
        self.model = None
        self.utils = None
        self.threshold = threshold
        
        try:
            nervous_system.sensory("Inicializando Silero VAD...")
            
            # Load model securely options
            torch.set_num_threads(1)
            
            # Load from torch.hub (will download on first run)
            # Using local path if available to avoid constant downloads
            self.model, self.utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=True  # Use ONNX for speed if available via onnxruntime
            )
            
            (self.get_speech_timestamps,
             self.save_audio,
             self.read_audio,
             self.VADIterator,
             self.collect_chunks) = self.utils
             
            # self.model.eval()  # Not needed/supported for ONNX model
            nervous_system.sensory("✓ Silero VAD cargado exitosamente")
            
        except Exception as e:
            nervous_system.error("SENSORY", f"Error cargando Silero VAD: {e}")
            self.model = None

    def is_speech(self, audio_chunk, sample_rate=16000):
        """
        Check if audio chunk contains speech
        
        Args:
            audio_chunk: Raw audio bytes or float array
            sample_rate: Audio sample rate (must be 8000 or 16000 for Silero)
        
        Returns:
            bool: True if speech detected
        """
        if self.model is None:
            return True  # Fallback: assume speech if model failed
            
        try:
            # Convert audio bytes to tensor if needed
            if isinstance(audio_chunk, bytes):
                # Convert 16-bit PCM bytes to float32 tensor normalized to [-1, 1]
                audio_int16 = np.frombuffer(audio_chunk, dtype=np.int16)
                audio_float32 = audio_int16.astype(np.float32) / 32768.0
                tensor = torch.from_numpy(audio_float32)
            else:
                tensor = audio_chunk
            
            # Get speech probability
            speech_prob = self.model(tensor, sample_rate).item()
            return speech_prob > self.threshold
            
        except Exception as e:
            # Don't spam errors on every chunk, but log occasionally?
            # For now silent fail to True to avoid blocking
            return True
            
    def process(self, audio_chunk):
        """Alias for is_speech compatible with other engines"""
        return self.is_speech(audio_chunk)

    def is_available(self):
        return self.model is not None
