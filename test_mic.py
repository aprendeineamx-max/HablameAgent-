import speech_recognition as sr
import sys

# Forzar codificación utf-8 para la consola
sys.stdout.reconfigure(encoding='utf-8')

print("--- DIAGNOSTICO DE MICROFONO ---")
print("Buscando microfonos disponibles...")
try:
    mics = sr.Microphone.list_microphone_names()
    
    if not mics:
        print("[ERROR] No se encontraron microfonos.")
    else:
        print(f"\nEncontrados {len(mics)} dispositivos:")
        for index, name in enumerate(mics):
            try:
                print(f"Index {index}: {name}")
            except:
                print(f"Index {index}: [Nombre con caracteres no imprimibles]")

        print("\n------------------------------------------------")
        print("Prueba de Escucha (5 segundos) con Micrófono por Defecto:")
        r = sr.Recognizer()
        r.energy_threshold = 1000 # El valor que pusimos en el codigo
        r.dynamic_energy_threshold = False
        
        try:
            with sr.Microphone() as source:
                print(f" -> Usando dispositivo por defecto: {source.device_index}")
                print(" -> Ajustando ruido ambiente (1s)...")
                r.adjust_for_ambient_noise(source, duration=1)
                print(f" -> Ruido base detectado (energy threshold ajustado): {r.energy_threshold}")
                
                print(" -> !!! HABLA AHORA (Di 'Hola') !!!")
                try:
                    # Timeout corto para no bloquear si no escucha
                    audio = r.listen(source, timeout=5, phrase_time_limit=5)
                    print(" -> Audio capturado.")
                    
                    print(" -> Intentando reconocer con Google...")
                    try:
                        text = r.recognize_google(audio, language="es-ES")
                        print(f" -> EXITO! Texto reconocido: '{text}'")
                    except sr.UnknownValueError:
                        print(" -> [FALLO] Audio capturado pero no se entendieron palabras (Ruido/Silencio).")
                    except sr.RequestError as e:
                        print(f" -> [ERROR] Error de conexión con Google: {e}")
                        
                except sr.WaitTimeoutError:
                    print(" -> [TIMEOUT] No se detectó voz en 5 segundos.")
                    
        except Exception as e:
            print(f" -> [CRITICAL] No se pudo abrir el microfono. Error: {e}")

except Exception as e:
    print(f"[FATAL] Error listando microfonos: {e}")

print("--- FIN DIAGNOSTICO ---")
