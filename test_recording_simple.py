"""
Simple standalone recording test
This bypasses all UI and just tests if PyAudio can record from the mic
"""
import pyaudio
import wave
import numpy as np
from datetime import datetime
import os

# Find WO Mic
def find_wo_mic():
    p = pyaudio.PyAudio()
    print("\n=== Available Microphones ===")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        name = info['name']
        print(f"[{i}] {name} (inputs: {info['maxInputChannels']})")
        if 'wo mic' in name.lower() and 'wave' in name.lower():
            print(f"  ^^^ FOUND WO MIC WAVE at index {i}")
            p.terminate()
            return i
    p.terminate()
    return None

# Record function
def record_audio(device_idx, duration_seconds=5):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    
    p = pyaudio.PyAudio()
    
    print(f"\n=== Opening stream for device {device_idx} ===")
    try:
        stream = p.open(format=FORMAT,
                       channels=CHANNELS,
                       rate=RATE,
                       input=True,
                       input_device_index=device_idx,
                       frames_per_buffer=CHUNK)
        print("Stream opened successfully!")
    except Exception as e:
        print(f"ERROR opening stream: {e}")
        p.terminate()
        return None
    
    print(f"\n*** RECORDING FOR {duration_seconds} SECONDS ***")
    print("Speak now...")
    
    frames = []
    for i in range(0, int(RATE / CHUNK * duration_seconds)):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
        
        # Show progress
        if i % 10 == 0:
            audio_array = np.frombuffer(data, dtype=np.int16)
            rms = np.sqrt(np.mean(audio_array**2))
            db = 20 * np.log10(rms) if rms > 0 else -60
            print(f"  [{i}/{int(RATE / CHUNK * duration_seconds)}] dB: {db:.1f}")
    
    print(f"\n*** RECORDING STOPPED - Captured {len(frames)} chunks ***")
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # Save file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_rec_{timestamp}.wav"
    filepath = os.path.join(os.path.dirname(__file__), filename)
    
    print(f"\n=== Saving to: {filepath} ===")
    wf = wave.open(filepath, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    # Check file size
    size = os.path.getsize(filepath)
    print(f"File saved! Size: {size} bytes ({size/1024:.2f} KB)")
    
    return filepath

if __name__ == "__main__":
    print("="*60)
    print("STANDALONE RECORDING TEST")
    print("="*60)
    
    mic_idx = find_wo_mic()
    
    if mic_idx is None:
        print("\nERROR: WO Mic not found!")
        print("Please select mic index manually:")
        mic_idx = int(input("Enter device index: "))
    
    filepath = record_audio(mic_idx, duration_seconds=5)
    
    if filepath:
        print(f"\n{'='*60}")
        print(f"SUCCESS! File saved to:")
        print(f"  {filepath}")
        print(f"{'='*60}")
        
        # Try to play it
        import os
        os.startfile(filepath)
    else:
        print("\nFAILED to record.")
