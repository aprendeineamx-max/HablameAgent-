import sys
import threading
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThread, Signal, QObject, Slot

from core.config import settings
from core.ear import Ear
from core.brain import Brain
from core.voice import Voice
from core.action_engine import AutomationEngine
from ui.overlay import ControlPanel
from core.logger import nervous_system

# Worker para correr el agente en segundo plano sin congelar la UI
class AgentWorker(QObject):
    status_changed = Signal(str, str) # Mensaje, Estado
    text_recognized = Signal(str, str) # Mensaje, Tipo (user/agent)
    
    def __init__(self):
        super().__init__()
        nervous_system.system("Inicializando Worker Thread...")
        self.ear = Ear()
        self.voice = Voice()
        self.brain = Brain()
        self.hands = AutomationEngine()
        self.wake_word = settings.WAKE_WORD.lower()
        self.running = True
        self.paused = False

    @Slot(int)
    def change_microphone(self, index):
        success = self.ear.set_device_index(index)
        if success:
            self.status_changed.emit("Micrófono cambiado", "idle")
            self.text_recognized.emit(f"Micrófono cambiado a índice {index}", "agent")

    @Slot()
    def toggle_pause(self):
        self.paused = not self.paused
        status = "Pausado" if self.paused else "Reanudado"
        self.status_changed.emit(status, "idle")
        self.text_recognized.emit(f"Sistema {status.lower()}.", "agent")

    def run(self):
        nervous_system.system("Agente activo y listo.")
        self.status_changed.emit("Iniciado. Di 'Computadora'", "idle")
        self.voice.speak("Sistema en línea.")

        while self.running:
            if self.paused:
                time.sleep(1)
                continue

            # Estado IDLE / ESCUCHANDO
            self.status_changed.emit("Escuchando...", "listening")
            user_text = self.ear.listen()

            if not user_text:
                self.status_changed.emit("...", "idle")
                time.sleep(0.5)
                continue

            user_text = user_text.lower()
            self.text_recognized.emit(user_text, "user")
            
            if self.wake_word in user_text or True: # Demo mode: siempre activo
                command = user_text.replace(self.wake_word, "").strip()
                if not command: continue

                # PENSANDO
                self.status_changed.emit("Procesando...", "thinking")
                
                # Inteligencia
                action_plan = self.brain.think(command)
                self.text_recognized.emit(f"Plan: {action_plan}", "agent")
                
                # ACTUANDO
                self.status_changed.emit("Ejecutando...", "speaking")
                if action_plan:
                    success = self.hands.execute_task(action_plan)
                    if success:
                        self.status_changed.emit("Listo", "idle")
                    else:
                        nervous_system.error("SYSTEM", "Fallo durante la ejecución.")
                        self.status_changed.emit("Error", "idle")
                else:
                    self.voice.speak("No entendí.")
                    self.status_changed.emit("No entendido", "idle")
            
            time.sleep(0.5)

    def stop(self):
        self.running = False

def main():
    nervous_system.system("ARQUITECTURA DE ACCESIBILIDAD CARGANDO...")
    app = QApplication(sys.argv)
    
    
    # Pre-detect microphone before UI loads
    nervous_system.system("Configurando dispositivos de audio...")
    try:
        # Create a temporary Ear instance just to trigger finding the mic
        # The auto-detection runs in Ear.__init__ if settings.MIC_DEVICE_INDEX is None
        temp_ear = Ear() 
        # Now settings.MIC_DEVICE_INDEX should be set to WO Mic if found
        nervous_system.system(f"Micrófono pre-seleccionado: {settings.MIC_DEVICE_INDEX}")
    except Exception as e:
        nervous_system.error("SYSTEM", f"Fallo en pre-detección de micro: {e}")

    # Crear UI
    nervous_system.system("Cargando Panel de Control...")
    overlay = ControlPanel()
    
    # Connect logger to UI
    nervous_system.set_ui_callback(overlay.append_system_log)
    
    overlay.show()
    
    # Crear Hilo del Agente (Lógica)
    thread = QThread()
    worker = AgentWorker()
    worker.moveToThread(thread)
    
    # Conectar señales
    thread.started.connect(worker.run)
    
    # Signals Worker -> UI
    worker.status_changed.connect(overlay.update_status)
    worker.text_recognized.connect(overlay.append_log)
    
    # Signals UI -> Worker
    overlay.microphone_changed.connect(worker.change_microphone)
    overlay.pause_toggled.connect(worker.toggle_pause)
    
    # Iniciar
    thread.start()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
