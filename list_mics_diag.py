import speech_recognition as sr
import pyaudio

print("--- SPEECH RECOGNITION DEVICES ---")
try:
    mics = sr.Microphone.list_microphone_names()
    for i, mic in enumerate(mics):
        try:
            # Handle encoding for display
            name = mic.encode('cp1252').decode('utf-8')
        except:
            name = mic
        print(f"Index {i}: {name}")
except Exception as e:
    print(f"Error getting SR mics: {e}")

print("\n--- PYAUDIO DEVICES ---")
try:
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    for i in range(0, numdevices):
        if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
            name = p.get_device_info_by_host_api_device_index(0, i).get('name')
            try:
                name = name.encode('cp1252').decode('utf-8')
            except: pass
            print(f"Index {i}: {name}")
    p.terminate()
except Exception as e:
    print(f"Error getting PyAudio mics: {e}")
