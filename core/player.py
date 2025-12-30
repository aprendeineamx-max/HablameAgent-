
import sounddevice as sd
import soundfile as sf
import numpy as np
import threading
from core.logger import nervous_system

class AudioPlayer:
    def __init__(self):
        self.stream = None
        self.stop_event = threading.Event()
        self.is_playing = False

    def play(self, data, samplerate):
        """Play numpy array audio data"""
        self.stop() # Stop any current playback
        self.stop_event.clear()
        self.is_playing = True
        
        def _play():
            try:
                sd.play(data, samplerate)
                sd.wait() # Wait until done or stopped
            except Exception as e:
                nervous_system.error("PLAYER", f"Error playing audio: {e}")
            finally:
                self.is_playing = False
                
        # sounddevice.play is non-blocking (starts a stream), but sd.wait() blocks.
        # However, sd.play doesn't return a handle to stop easily unless we use OutputStream.
        # Actually sd.stop() stops all playback.
        
        try:
            sd.play(data, samplerate)
            # We don't sd.wait() here because we want to be non-blocking to the main thread?
            # But Voice.speak() is usually expected to block?
            # No, for Barge-in we want it NON-blocking or blocking-but-interruptible.
            sd.wait()
        except Exception as e:
             nervous_system.error("PLAYER", f"Playback error: {e}")

    def play_file(self, filename):
        """Play an audio file"""
        try:
            data, fs = sf.read(filename, dtype='float32')
            self.play(data, fs)
        except Exception as e:
            nervous_system.error("PLAYER", f"Error reading file {filename}: {e}")

    def stop(self):
        """Stop current playback immediately"""
        if self.is_playing or True: # sounddevice tracks state globally mostly
            try:
                sd.stop()
                self.is_playing = False
            except Exception as e:
                pass
