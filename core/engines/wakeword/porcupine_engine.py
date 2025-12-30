"""
Porcupine Engine - Local Wake Word Detection
Uses Picovoice Porcupine for efficient keyword spotting
"""
import pvporcupine
import struct
import platform
import os
from core.logger import nervous_system
from core.config import settings

class PorcupineEngine:
    def __init__(self, access_key=None, keywords=None):
        """
        Initialize Porcupine
        
        Args:
            access_key: Picovoice AccessKey (default from settings)
            keywords: List of keywords (default: ['jarvis', 'computer'])
        """
        self.access_key = access_key or getattr(settings, "PICOVOICE_ACCESS_KEY", None)
        self.porcupine = None
        self.keywords = keywords or ["jarvis", "computer"]
        
        if not self.access_key:
            nervous_system.sensory("Porcupine: No AccessKey found. Wake Word disabled.")
            return

        try:
            nervous_system.sensory(f"Inicializando Porcupine Wake Word ({self.keywords})...")
            
            self.porcupine = pvporcupine.create(
                access_key=self.access_key,
                keywords=self.keywords
            )
            
            nervous_system.sensory(f"✓ Porcupine listo. Palabras clave: {self.keywords}")
            
        except Exception as e:
            nervous_system.error("SENSORY", f"Error cargando Porcupine: {e}")
            self.porcupine = None

    def process(self, audio_chunk):
        """
        Process audio chunk for wake word
        
        Args:
            audio_chunk: Raw audio bytes (PCM 16-bit)
            
        Returns:
            int: Index of keyword detected, or -1 if none
        """
        if self.porcupine is None:
            return -1
            
        try:
            # Porcupine expects text frame (512 samples usually)
            # Need to ensure chunk matches expected frame length
            
            # Convert bytes to tuple of shorts
            pcm = struct.unpack_from("h" * self.porcupine.frame_length, audio_chunk)
            
            keyword_index = self.porcupine.process(pcm)
            return keyword_index
            
        except struct.error:
            # Chunk size mismatch - Porcupine is very strict about frame size
            # This engine usually requires a dedicated loop that feeds exact frame sizes
            return -1
        except Exception as e:
            nervous_system.error("SENSORY", f"Porcupine error: {e}")
            return -1

    def get_frame_length(self):
        """Return required required frame length (number of samples)"""
        if self.porcupine:
            return self.porcupine.frame_length
        return 512

    def delete(self):
        if self.porcupine:
            self.porcupine.delete()

    def is_available(self):
        return self.porcupine is not None
