import sys
import pyaudio
import numpy as np
import wave
import os
import datetime
import subprocess

from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, 
                               QHBoxLayout, QComboBox, QTextEdit, QPushButton, 
                               QFrame, QGraphicsDropShadowEffect, QSizePolicy, 
                               QProgressBar, QLCDNumber)
from PySide6.QtCore import Qt, QTimer, Slot, QPoint, QSize, Signal, QThread, QRectF
from PySide6.QtGui import QColor, QPainter, QBrush, QFont, QRadialGradient, QIcon, QPainterPath, QPen, QLinearGradient

from core.config import settings
from core.ear import Ear

# --- PROFESSIONAL THEME ---
THEME = {
    "bg": "#121212",
    "panel_bg": "#1e1e1e",
    "accent": "#00e5ff", # Cyan
    "accent_dim": "rgba(0, 229, 255, 0.3)",
    "text_main": "#ffffff",
    "text_dim": "#888888",
    "danger": "#ff3333",
    "success": "#00ff88",
    "font_main": "Segoe UI",
    "font_mono": "Consolas"
}

STYLESHEET = f"""
QWidget {{
    background-color: transparent;
    color: {THEME['text_main']};
    font-family: '{THEME['font_main']}', sans-serif;
}}
QFrame#MainPanel {{
    background-color: {THEME['panel_bg']};
    border: 1px solid #333;
    border-radius: 8px;
}}
QComboBox {{
    background-color: #2a2a2a;
    border: 1px solid #444;
    border-radius: 4px;
    padding: 4px;
    color: {THEME['accent']};
    font-family: '{THEME['font_mono']}';
    font-size: 11px;
}}
QComboBox::drop-down {{ border: none; }}
QPushButton {{
    background-color: #2a2a2a;
    border: 1px solid #444;
    border-radius: 4px;
    padding: 6px;
    font-weight: bold;
    font-size: 11px;
}}
QPushButton:hover {{
    border-color: {THEME['accent']};
    color: {THEME['accent']};
}}
QPushButton#RecButton {{
    color: {THEME['danger']};
    border-color: {THEME['danger']};
}}
QPushButton#RecButton:checked {{
    background-color: {THEME['danger']};
    color: white;
}}
QTextEdit {{
    background-color: #111;
    border: 1px solid #333;
    border-radius: 4px;
    font-family: '{THEME['font_mono']}';
    font-size: 10px;
    color: #ccc;
}}
QLabel#Header {{
    font-weight: bold;
    font-size: 14px;
    color: {THEME['accent']};
    letter-spacing: 1px;
}}
QLCDNumber {{
    border: none;
    color: {THEME['accent']};
}}
"""

class WaveformWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self.buffer = np.zeros(512, dtype=np.float32)
        self.setStyleSheet("background-color: #000; border: 1px solid #333; border-radius: 4px;")
        
    def update_data(self, data_bytes):
        """Recibe bytes raw de audio, decodifica y actualiza buffer"""
        try:
            # Convert audio bytes to int16 numpy array
            data_np = np.frombuffer(data_bytes, dtype=np.int16)
            # Normalize to -1.0 ... 1.0
            data_float = data_np.astype(np.float32) / 32768.0
            
            # Simple downsampling/resizing to fit our display buffer
            # We want to show a moving window or just the current chunk
            # For a slick effect, let's just visualize the current chunk stretched
            if len(data_float) > 0:
                self.buffer = data_float[:512] # Take first 512 samples
                if len(self.buffer) < 512:
                     self.buffer = np.pad(self.buffer, (0, 512 - len(self.buffer)))
            self.update()
        except Exception:
            pass

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor("#111"))
        
        # Grid lines
        painter.setPen(QPen(QColor("#222"), 1))
        mw = self.width()
        mh = self.height()
        cy = mh / 2
        
        painter.drawLine(0, int(cy), mw, int(cy)) # Center line
        
        # Draw Waveform
        path = QPainterPath()
        path.moveTo(0, cy)
        
        step_x = mw / len(self.buffer)
        
        for i, sample in enumerate(self.buffer):
            x = i * step_x
            # Amplify for visual clarity
            y = cy - (sample * mh * 0.8) 
            path.lineTo(x, y)
            
        # Gradient Brush
        gradient = QLinearGradient(0, 0, mw, 0)
        gradient.setColorAt(0.0, QColor(THEME['accent_dim']))
        gradient.setColorAt(0.5, QColor(THEME['accent']))
        gradient.setColorAt(1.0, QColor(THEME['accent_dim']))
        
        pen = QPen(QBrush(gradient), 1.5)
        painter.setPen(pen)
        painter.drawPath(path)


class AudioMonitorThread(QThread):
    raw_data_available = Signal(bytes)
    level_decibel = Signal(float)
    recording_finished = Signal(str)

    def __init__(self, device_index):
        super().__init__()
        self.device_index = device_index
        self.running = True
        self.recording = False
        self.frames = []
        self.p = pyaudio.PyAudio()
        self.chunk = 1024
        self.rate = 44100

    def run(self):
        print(f"[MONITOR] Thread started for device {self.device_index}")
        try:
            stream = self.p.open(format=pyaudio.paInt16,
                                 channels=1,
                                 rate=self.rate,
                                 input=True,
                                 input_device_index=self.device_index,
                                 frames_per_buffer=self.chunk)
            print(f"[MONITOR] Stream opened successfully")
            
            chunk_count = 0
            while self.running:
                data = stream.read(self.chunk, exception_on_overflow=False)
                chunk_count += 1
                
                # Emit raw for visualization
                self.raw_data_available.emit(data)
                
                # Calculate dB
                audio_array = np.frombuffer(data, dtype=np.int16)
                rms = np.sqrt(np.mean(audio_array**2))
                db = 20 * np.log10(rms) if rms > 0 else -60
                self.level_decibel.emit(db)
                
                if self.recording:
                    self.frames.append(data)
                    if chunk_count % 100 == 0:  # Log every 100 chunks
                        print(f"[MONITOR] Recording... {len(self.frames)} chunks captured")

            stream.stop_stream()
            stream.close()
            print(f"[MONITOR] Stream closed. Total chunks processed: {chunk_count}")
        except Exception as e:
            print(f"[MONITOR] ERROR in run(): {e}")
        finally:
            self.p.terminate()
            print(f"[MONITOR] PyAudio terminated")

    def start_recording(self):
        print(f"[MONITOR] start_recording() called")
        self.frames = []
        self.recording = True
        print(f"[MONITOR] Recording flag set to True, frames cleared")

    def stop_recording(self):
        self.recording = False
        # Small sleep to allow last chunk to be processed
        import time; time.sleep(0.1) 
        return self._save_file()

    def _save_file(self):
        if not self.frames: 
            print("ERROR: No frames captured!")
            return None
            
        # Ensure proper directory relative to the script/executable location
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        rec_dir = os.path.join(base_dir, "Recordings")
        os.makedirs(rec_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"rec_{timestamp}.wav"
        filepath = os.path.join(rec_dir, filename)
        
        try:
            wf = wave.open(filepath, 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(self.frames))
            wf.close()
            print(f"DEBUG: Saved {filepath} with {len(self.frames)} chunks.")
            self.recording_finished.emit(filepath)
            return filepath
        except Exception as e:
            print(f"ERROR Saving WAV: {e}")
            return None

    def stop(self):
        self.running = False


class ControlPanel(QWidget):
    # Signals
    microphone_changed = Signal(int)
    pause_toggled = Signal()
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet(STYLESHEET)
        
        self.monitor = None
        self.last_path = None
        self.is_recording = False
        self.recording_start_time = None
        
        self.init_ui()
        self.setup_timers()

    def init_ui(self):
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        # --- MAIN FRAME ---
        self.frame = QFrame()
        self.frame.setObjectName("MainPanel")
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setColor(QColor(0,0,0,200)); shadow.setOffset(0,0)
        self.frame.setGraphicsEffect(shadow)
        
        self.layout_frame = QVBoxLayout(self.frame)
        self.layout_frame.setSpacing(10)
        
        # 1. HEADER (Title + Close)
        header = QHBoxLayout()
        lbl_title = QLabel("HABLAME // SYSTEM CORE")
        lbl_title.setObjectName("Header")
        
        btn_close = QPushButton("×")
        btn_close.setFixedSize(24, 24)
        btn_close.clicked.connect(self.close_app)
        btn_close.setStyleSheet("border:none; color:#666; font-size:16px;")
        
        header.addWidget(lbl_title)
        header.addStretch()
        header.addWidget(btn_close)
        self.layout_frame.addLayout(header)
        
        # 2. STATUS INFO (Mic Name | dB)
        info_row = QHBoxLayout()
        self.lbl_mic_info = QLabel("MIC: Initializing...")
        self.lbl_mic_info.setStyleSheet(f"color: {THEME['text_dim']}; font-family: Consolas; font-size:10px;")
        
        self.lbl_db = QLabel("-INF dB")
        self.lbl_db.setStyleSheet(f"color: {THEME['accent']}; font-family: Consolas; font-weight:bold;")
        
        info_row.addWidget(self.lbl_mic_info)
        info_row.addStretch()
        info_row.addWidget(self.lbl_db)
        self.layout_frame.addLayout(info_row)
        
        # 3. WAVEFORM (The Real Deal)
        self.waveform = WaveformWidget()
        self.layout_frame.addWidget(self.waveform)
        
        # 4. LOG TERMINAL
        self.log_area = QTextEdit()
        self.log_area.setFixedHeight(100)
        self.log_area.setPlaceholderText(">> System ready. Waiting for input...")
        self.layout_frame.addWidget(self.log_area)
        
        # 5. CONTROLS DECK
        deck = QHBoxLayout()
        deck.setSpacing(5)
        
        # Mic Selector
        self.combo_mics = QComboBox()
        self.populate_mics()
        self.combo_mics.currentIndexChanged.connect(self.on_mic_change)
        
        btn_refresh = QPushButton("↺")
        btn_refresh.setFixedSize(24, 24)
        btn_refresh.clicked.connect(self.populate_mics)
        
        deck.addWidget(self.combo_mics, 1)
        deck.addWidget(btn_refresh)
        
        self.layout_frame.addLayout(deck)
        
        
        # 6. ACTION DECK - SIMPLIFIED (No recording until core works)
        actions = QHBoxLayout()
        
        self.btn_pause = QPushButton("⏸ PAUSE AGENT")
        self.btn_pause.setCheckable(True)
        self.btn_pause.clicked.connect(self.toggle_pause)
        
        actions.addWidget(self.btn_pause)
        actions.addStretch()
        
        self.layout_frame.addLayout(actions)
        
        # 7. SYSTEM LOGS (Real-time nervous_system output)
        log_label = QLabel("SYSTEM LOGS:")
        log_label.setStyleSheet(f"color: {THEME['text_dim']}; font-size: 9px; font-weight: bold;")
        self.layout_frame.addWidget(log_label)
        
        self.system_log_area = QTextEdit()
        self.system_log_area.setReadOnly(True)
        self.system_log_area.setFixedHeight(120)
        self.system_log_area.setPlaceholderText(">> Waiting for system logs...")
        self.system_log_area.setStyleSheet(f"""
            background-color: #000;
            border: 1px solid #333;
            border-radius: 4px;
            font-family: '{THEME['font_mono']}';
            font-size: 9px;
            color: #0f0;
        """)
        self.layout_frame.addWidget(self.system_log_area)
        
        self.main_layout.addWidget(self.frame)
        
        # Geometry
        self.resize(450, 500) # Slightly wider
        self.center_screen()

    def setup_timers(self):
        self.rec_timer = QTimer(self)
        self.rec_timer.timeout.connect(self.update_rec_timer)

    def center_screen(self):
        screen = QApplication.primaryScreen().geometry()
        x = screen.width() - self.width() - 20
        y = screen.height() - self.height() - 60
        self.move(x, y)

    # --- LOGIC ---
    
    def populate_mics(self):
        self.combo_mics.blockSignals(True)
        self.combo_mics.clear()
        mics = Ear.list_microphones()
        for i, m in enumerate(mics):
            try: name = m.encode('latin-1').decode('utf-8')
            except: name = m
            self.combo_mics.addItem(f"[{i}] {name}", i)
        
        # Restore selection
        idx = settings.MIC_DEVICE_INDEX
        if idx is not None:
             ui_idx = self.combo_mics.findData(idx)
             if ui_idx >= 0: self.combo_mics.setCurrentIndex(ui_idx)
        self.combo_mics.blockSignals(False)

    def start_monitor(self, device_index):
        if self.monitor: self.stop_monitor()
        self.monitor = AudioMonitorThread(device_index)
        self.monitor.raw_data_available.connect(self.waveform.update_data)
        self.monitor.level_decibel.connect(self.update_db_label)
        self.monitor.recording_finished.connect(self.on_rec_finished)
        self.monitor.start()
        
        # Update Label
        current_text = self.combo_mics.currentText()
        self.lbl_mic_info.setText(f"MIC: {current_text}")

    def stop_monitor(self):
        if self.monitor:
            self.monitor.stop()
            self.monitor.wait()
            self.monitor = None

    @Slot(int)
    def on_mic_change(self, index):
        real_idx = self.combo_mics.currentData()
        self.microphone_changed.emit(real_idx)
        # If we are monitoring (recording or testing), restart
        # For now, let's keep monitor OFF unless REC/TEST is active?
        # User wants REAL visualizer always. So we might need to auto-start it 
        # BUT this conflicts with Ear.py if we don't handle it.
        # Strategy: Auto-start monitor for visualization. 
        # Ear.py needs to be paused OR we rely on OS mixing (which fails on generic PyAudio).
        # Let's auto-start monitor for now, and rely on PAUSE AGENT to fix conflicts if they happen.
        self.start_monitor(real_idx)

    @Slot(float)
    def update_db_label(self, db):
        self.lbl_db.setText(f"{db:.1f} dB")

    @Slot()
    def toggle_rec(self):
        print(f"[UI] toggle_rec() called, btn_rec.isChecked() = {self.btn_rec.isChecked()}")
        if self.btn_rec.isChecked():
            # START
            print(f"[UI] Starting recording...")
            if not self.monitor:
                print(f"[UI] No monitor active, starting new monitor")
                self.start_monitor(self.combo_mics.currentData())
            else:
                print(f"[UI] Monitor already active")
            
            # Ensure agent is paused to avoid conflict if not already
            if not self.btn_pause.isChecked():
                print(f"[UI] Auto-pausing agent")
                self.btn_pause.click() # Simulate click to toggle pause ON
            
            self.monitor.start_recording()
            self.recording_start_time = datetime.datetime.now()
            self.rec_timer.start(100)
            self.log("Recording started...", "sys")
        else:
            # STOP
            print(f"[UI] Stopping recording...")
            self.rec_timer.stop()
            if self.monitor:
                print(f"[UI] Calling monitor.stop_recording()")
                path = self.monitor.stop_recording()
                print(f"[UI] stop_recording() returned: {path}")
                # We don't stop monitor, we just stop saving frames
                # so visualizer keeps running
            else:
                print(f"[UI] ERROR: No monitor to stop!")
            self.log("Recording stopped.", "sys")

    def update_rec_timer(self):
        if self.recording_start_time:
            delta = datetime.datetime.now() - self.recording_start_time
            # Format MM:SS
            total_seconds = int(delta.total_seconds())
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            self.lcd_timer.display(f"{minutes:02}:{seconds:02}")
    @Slot(str)
    def on_rec_finished(self, path):
        print(f"[UI] on_rec_finished() called with path: {path}")
        self.last_path = path
        self.btn_play.setEnabled(True)
        self.log(f"Saved: {os.path.basename(path)}", "success")
        # Ensure path is absolute for safety
        self.last_path = os.path.abspath(path)
        print(f"[UI] Play button enabled, last_path set to: {self.last_path}")

    @Slot()
    def play_last(self):
        if self.last_path and os.path.exists(self.last_path):
            self.log(f"Playing: {self.last_path}", "sys")
            try:
                if os.name == 'nt':
                    os.startfile(self.last_path)
                else:
                    subprocess.call(['open', self.last_path])
            except Exception as e:
                self.log(f"Error playing: {e}", "warn")
        else:
             self.log("No file found.", "warn")

    @Slot()
    def open_rec_folder(self):
        rec_dir = os.path.join(os.getcwd(), "Recordings")
        if not os.path.exists(rec_dir):
            os.makedirs(rec_dir)
        try:
            if os.name == 'nt':
                os.startfile(rec_dir)
            else:
                subprocess.call(['open', rec_dir])
            self.log(f"Opened: {rec_dir}", "sys")
        except Exception as e:
            self.log(f"Error opening folder: {e}", "warn")

    @Slot()
    def toggle_pause(self):
        self.pause_toggled.emit()
        if self.btn_pause.isChecked():
            self.btn_pause.setText("▶ RESUME AGENT")
            self.btn_pause.setStyleSheet(f"color: {THEME['danger']}; border-color: {THEME['danger']};")
            self.log("Agent System Paused.", "warn")
            
            # Depuis Agent is paused, we can safely start monitor if not running
            if not self.monitor and self.combo_mics.currentData() is not None:
                self.start_monitor(self.combo_mics.currentData())
                
        else:
            self.btn_pause.setText("⏸ PAUSE AGENT")
            self.btn_pause.setStyleSheet("")
            self.log("Agent System Resumed.", "success")
            # If we were strictly monitoring for visual only, we might need to stop?
            # If conflict persists:
            # self.stop_monitor() 

    def log(self, text, level="info"):
        color = "#ccc"
        if level == "warn": color = THEME['danger']
        if level == "success": color = THEME['success']
        if level == "sys": color = THEME['accent']
        
        self.log_area.append(f'<span style="color:{color}">> {text}</span>')
        self.log_area.verticalScrollBar().setValue(self.log_area.verticalScrollBar().maximum())
        
    def append_log(self, text, type="agent"):
        # Compatibility with main.py
        self.log(text, type)
    
    def append_system_log(self, text):
        """Append to the system log viewer (green terminal-style)"""
        self.system_log_area.append(text)
        self.system_log_area.verticalScrollBar().setValue(
            self.system_log_area.verticalScrollBar().maximum()
        )

    def update_status(self, text, state="idle"):
        # Compatibility with main.py
        self.log(f"STATUS: {text} ({state})", "sys")

    # Draggable
    def mousePressEvent(self, event):
        self.old_pos = event.globalPos()
    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPos() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()
    def mouseReleaseEvent(self, event):
        self.old_pos = None
    
    def close_app(self):
        self.stop_monitor()
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ControlPanel()
    win.show()
    sys.exit(app.exec())
