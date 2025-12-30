import sys
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, 
                               QHBoxLayout, QComboBox, QTextEdit, QPushButton, 
                               QFrame, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor

from core.config import settings
from core.ear import Ear

# --- PROFESSIONAL THEME ---
THEME = {
    "bg": "#121212",
    "panel_bg": "#1e1e1e",
    "accent": "#00e5ff",  # Cyan
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
"""


class ControlPanel(QWidget):
    # Signals
    microphone_changed = Signal(int)
    pause_toggled = Signal()
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet(STYLESHEET)
        
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        # --- MAIN FRAME ---
        self.frame = QFrame()
        self.frame.setObjectName("MainPanel")
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 200))
        shadow.setOffset(0, 0)
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
        
        # 2. STATUS INFO (Mic Name)
        info_row = QHBoxLayout()
        self.lbl_mic_info = QLabel("MIC: Initializing...")
        self.lbl_mic_info.setStyleSheet(f"color: {THEME['text_dim']}; font-family: Consolas; font-size:10px;")
        
        self.lbl_status = QLabel("● READY")
        self.lbl_status.setStyleSheet(f"color: {THEME['success']}; font-family: Consolas; font-weight:bold;")
        
        info_row.addWidget(self.lbl_mic_info)
        info_row.addStretch()
        info_row.addWidget(self.lbl_status)
        self.layout_frame.addLayout(info_row)
        
        # 3. LOG TERMINAL (Main Area)
        self.log_area = QTextEdit()
        self.log_area.setFixedHeight(150)
        self.log_area.setPlaceholderText(">> System ready. Waiting for input...")
        self.layout_frame.addWidget(self.log_area)
        
        # 4. CONTROLS DECK
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
        
        # 5. ACTION DECK
        actions = QHBoxLayout()
        
        self.btn_pause = QPushButton("⏸ PAUSE AGENT")
        self.btn_pause.setCheckable(True)
        self.btn_pause.clicked.connect(self.toggle_pause)
        
        btn_admin = QPushButton("⚙ ADMIN")
        btn_admin.clicked.connect(self.open_admin_panel)
        btn_admin.setStyleSheet(f"border-color: {THEME['accent']}; color: {THEME['accent']};")
        
        actions.addWidget(self.btn_pause)
        actions.addWidget(btn_admin)
        actions.addStretch()
        
        self.layout_frame.addLayout(actions)
        
        # 6. SYSTEM LOGS (Real-time nervous_system output)
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
        self.resize(450, 450)
        self.center_screen()

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
            try:
                name = m.encode('latin-1').decode('utf-8')
            except:
                name = m
            self.combo_mics.addItem(f"[{i}] {name}", i)
        
        # Restore selection
        idx = settings.MIC_DEVICE_INDEX
        if idx is not None:
            ui_idx = self.combo_mics.findData(idx)
            if ui_idx >= 0:
                self.combo_mics.setCurrentIndex(ui_idx)
        self.combo_mics.blockSignals(False)
        
        # Update label
        current_text = self.combo_mics.currentText()
        self.lbl_mic_info.setText(f"MIC: {current_text}")

    @Slot(int)
    def on_mic_change(self, index):
        real_idx = self.combo_mics.currentData()
        self.microphone_changed.emit(real_idx)
        current_text = self.combo_mics.currentText()
        self.lbl_mic_info.setText(f"MIC: {current_text}")

    @Slot()
    def toggle_pause(self):
        self.pause_toggled.emit()
        if self.btn_pause.isChecked():
            self.btn_pause.setText("▶ RESUME AGENT")
            self.btn_pause.setStyleSheet(f"color: {THEME['danger']}; border-color: {THEME['danger']};")
            self.log("Agent System Paused.", "warn")
            self.lbl_status.setText("● PAUSED")
            self.lbl_status.setStyleSheet(f"color: {THEME['danger']};")
        else:
            self.btn_pause.setText("⏸ PAUSE AGENT")
            self.btn_pause.setStyleSheet("")
            self.log("Agent System Resumed.", "success")
            self.lbl_status.setText("● ACTIVE")
            self.lbl_status.setStyleSheet(f"color: {THEME['success']};")

    def log(self, text, level="info"):
        color = "#ccc"
        if level == "warn":
            color = THEME['danger']
        if level == "success":
            color = THEME['success']
        if level == "sys":
            color = THEME['accent']
        
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
        if hasattr(self, 'old_pos') and self.old_pos:
            delta = event.globalPos() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()
            
    def mouseReleaseEvent(self, event):
        self.old_pos = None
    
    def open_admin_panel(self):
        """Open the admin configuration panel"""
        from ui.admin_panel import AdminPanel
        panel = AdminPanel(self)
        panel.configuration_changed.connect(self._on_config_changed)
        panel.exec()
    
    def _on_config_changed(self):
        """Called when user changes configuration in admin panel"""
        self.log("Configuration updated! Restart may be required for changes to take effect.", "sys")
    
    def close_app(self):
        QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ControlPanel()
    win.show()
    sys.exit(app.exec())
