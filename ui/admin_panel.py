"""
Admin Panel - Technology Configuration Interface
Allows users to select and test different AI/automation technologies
"""
import sys
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QRadioButton, QButtonGroup,
                               QLineEdit, QFrame, QTabWidget, QWidget, QTextEdit,
                               QComboBox, QGroupBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from core.tech_manager import tech_manager
from core.logger import nervous_system


THEME = {
    "bg": "#1a1a1a",
    "panel": "#252525",
    "accent": "#00e5ff",
    "success": "#00ff88",
    "warning": "#ffaa00",
    "error": "#ff3333",
    "text": "#ffffff",
    "dim": "#888888"
}

STYLESHEET = f"""
QDialog {{
    background-color: {THEME['bg']};
    color: {THEME['text']};
    font-family: 'Segoe UI', sans-serif;
}}
QTabWidget::pane {{
    border: 1px solid #333;
    background: {THEME['panel']};
    border-radius: 4px;
}}
QTabBar::tab {{
    background: {THEME['panel']};
    color: {THEME['dim']};
    padding: 8px 16px;
    border: 1px solid #333;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}}
QTabBar::tab:selected {{
    background: {THEME['bg']};
    color: {THEME['accent']};
    border-bottom: 2px solid {THEME['accent']};
}}
QGroupBox {{
    border: 1px solid #444;
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 12px;
    color: {THEME['accent']};
    font-weight: bold;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}}
QRadioButton {{
    color: {THEME['text']};
    spacing: 8px;
}}
QRadioButton::indicator {{
    width: 16px;
    height: 16px;
}}
QRadioButton::indicator:checked {{
    background-color: {THEME['accent']};
    border: 2px solid {THEME['accent']};
    border-radius: 8px;
}}
QLineEdit {{
    background: #1a1a1a;
    border: 1px solid #444;
    border-radius: 4px;
    padding: 6px;
    color: {THEME['text']};
    font-family: 'Consolas';
}}
QPushButton {{
    background: #2a2a2a;
    border: 1px solid #444;
    border-radius: 4px;
    padding: 6px 12px;
    color: {THEME['text']};
    font-weight: bold;
}}
QPushButton:hover {{
    border-color: {THEME['accent']};
    color: {THEME['accent']};
}}
QPushButton#TestButton {{
    border-color: {THEME['success']};
    color: {THEME['success']};
}}
QPushButton#ApplyButton {{
    background: {THEME['accent']};
    color: #000;
    border: none;
}}
QPushButton#ApplyButton:hover {{
    background: #00d0e0;
}}
"""


class TechnologyTab(QWidget):
    """Base class for technology configuration tabs"""
    
    technology_changed = Signal(str, str)  # (category, engine_name)
    
    def __init__(self, category: str, parent=None):
        super().__init__(parent)
        self.category = category
        self.button_group = QButtonGroup(self)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Get available technologies for this category
        technologies = tech_manager.get_technologies(self.category)
        active_engine = tech_manager.get_active_engine(self.category)
        
        for engine_id, info in technologies.items():
            group_box = self._create_engine_group(engine_id, info, active_engine)
            layout.addWidget(group_box)
        
        layout.addStretch()
    
    def _create_engine_group(self, engine_id: str, info: dict, active_engine: str):
        """Create a group box for an engine"""
        group = QGroupBox(info.get("name", engine_id))
        layout = QVBoxLayout()
        
        # Radio button
        radio = QRadioButton("Use this engine")
        radio.setProperty("engine_id", engine_id)
        if engine_id == active_engine:
            radio.setChecked(True)
        
        self.button_group.addButton(radio)
        radio.toggled.connect(lambda checked, eid=engine_id: 
                             self._on_engine_selected(eid) if checked else None)
        
        layout.addWidget(radio)
        
        # Status indicator
        status = info.get("status", "unknown")
        status_text = {
            "active": f"✓ CONNECTED",
            "error": f"⚠ ERROR",
            "unknown": "⊗ NOT CONFIGURED"
        }.get(status, "⊗ UNKNOWN")
        
        status_color = {
            "active": THEME['success'],
            "error": THEME['error'],
            "unknown": THEME['dim']
        }.get(status, THEME['dim'])
        
        status_label = QLabel(f"Status: {status_text}")
        status_label.setStyleSheet(f"color: {status_color}; font-family: 'Consolas'; font-size: 11px;")
        layout.addWidget(status_label)
        
        # Error message if any
        if status == "error" and "error_msg" in info:
            error_label = QLabel(f"└ {info['error_msg']}")
            error_label.setStyleSheet(f"color: {THEME['error']}; font-size: 10px; padding-left: 20px;")
            layout.addWidget(error_label)
        
        # API Key field if required
        if info.get("requires_key", False):
            key_layout = QHBoxLayout()
            key_label = QLabel("API Key:")
            key_label.setStyleSheet(f"color: {THEME['dim']}; font-size: 10px;")
            
            key_input = QLineEdit()
            key_input.setEchoMode(QLineEdit.Password)
            key_input.setPlaceholderText("Enter API key...")
            key_input.setMaximumWidth(200)
            
            test_btn = QPushButton("🔄 Test")
            test_btn.setObjectName("TestButton")
            test_btn.setFixedWidth(70)
            test_btn.clicked.connect(lambda: self._test_engine(engine_id))
            
            key_layout.addWidget(key_label)
            key_layout.addWidget(key_input)
            key_layout.addWidget(test_btn)
            key_layout.addStretch()
            
            layout.addLayout(key_layout)
        
        # Additional info
        info_text = []
        if info.get("free", False):
            info_text.append("Cost: FREE")
        else:
            info_text.append("Cost: PAID")
        
        if info_text:
            info_label = QLabel(" | ".join(info_text))
            info_label.setStyleSheet(f"color: {THEME['dim']}; font-size: 9px; padding-left: 20px;")
            layout.addWidget(info_label)
        
        group.setLayout(layout)
        return group
    
    def _on_engine_selected(self, engine_id: str):
        """Called when user selects a different engine"""
        self.technology_changed.emit(self.category, engine_id)
        nervous_system.system(f"User selected {self.category}: {engine_id}")
    
    def _test_engine(self, engine_id: str):
        """Test if engine is working"""
        status, message = tech_manager.test_engine(self.category, engine_id)
        # TODO: Show result in a popup or status label
        nervous_system.system(f"Test {engine_id}: {status} - {message}")


class AdminPanel(QDialog):
    """Main admin panel dialog"""
    
    configuration_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("HABLAME // Admin Panel")
        self.setWindowFlags(Qt.Window)
        self.setStyleSheet(STYLESHEET)
        self.resize(600, 500)
        
        self.pending_changes = []
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header = QLabel("⚙ TECHNOLOGY CONFIGURATION")
        header_font = QFont("Segoe UI", 14, QFont.Bold)
        header.setFont(header_font)
        header.setStyleSheet(f"color: {THEME['accent']}; padding: 10px;")
        layout.addWidget(header)
        
        # Info Label
        info = QLabel("Select the technologies you want to use for each category")
        info.setStyleSheet(f"color: {THEME['dim']}; font-size: 10px; padding: 0 10px 10px 10px;")
        layout.addWidget(info)
        
        # Tabs
        tabs = QTabWidget()
        
        # STT Tab
        stt_tab = TechnologyTab("stt")
        stt_tab.technology_changed.connect(self._on_tech_changed)
        tabs.addTab(stt_tab, "🎤 Speech Recognition")
        
        # TTS Tab
        tts_tab = TechnologyTab("tts")
        tts_tab.technology_changed.connect(self._on_tech_changed)
        tabs.addTab(tts_tab, "🗣 Text-to-Speech")
        
        # LLM Tab
        llm_tab = TechnologyTab("llm")
        llm_tab.technology_changed.connect(self._on_tech_changed)
        tabs.addTab(llm_tab, "🧠 Language Model")
        
        # Motor Tab
        motor_tab = TechnologyTab("motor")
        motor_tab.technology_changed.connect(self._on_tech_changed)
        tabs.addTab(motor_tab, "✋ Motor Actions")
        
        # Wake Word Tab
        wake_tab = TechnologyTab("wake_word")
        wake_tab.technology_changed.connect(self._on_tech_changed)
        tabs.addTab(wake_tab, "🔊 Wake Word")
        
        # VAD Tab
        vad_tab = TechnologyTab("vad")
        vad_tab.technology_changed.connect(self._on_tech_changed)
        tabs.addTab(vad_tab, "🎙 Voice Activity")
        
        # Advanced Modules Tab
        advanced_tab = self._create_advanced_tab()
        tabs.addTab(advanced_tab, "⚡ Advanced Modules")
        
        layout.addWidget(tabs)
        
        # Stack Management
        stack_frame = QFrame()
        stack_layout = QHBoxLayout(stack_frame)
        
        stack_label = QLabel("Active Stack:")
        stack_label.setStyleSheet(f"color: {THEME['dim']};")
        
        self.stack_combo = QComboBox()
        stacks = tech_manager.get_all_stacks()
        for stack_name in stacks.keys():
            self.stack_combo.addItem(stack_name)
        
        current_stack = tech_manager.active_config.get("active_stack", "default")
        self.stack_combo.setCurrentText(current_stack)
        self.stack_combo.currentTextChanged.connect(self._on_stack_changed)
        
        save_stack_btn = QPushButton("💾 Save as New Stack")
        save_stack_btn.clicked.connect(self._save_stack)
        
        stack_layout.addWidget(stack_label)
        stack_layout.addWidget(self.stack_combo, 1)
        stack_layout.addWidget(save_stack_btn)
        
        layout.addWidget(stack_frame)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        
        apply_btn = QPushButton("Apply Changes")
        apply_btn.setObjectName("ApplyButton")
        apply_btn.clicked.connect(self._apply_changes)
        
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        button_layout.addWidget(apply_btn)
        
        layout.addLayout(button_layout)
    
    def _create_advanced_tab(self):
        """Create Advanced Modules tab showing optional enhancements"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Info header
        info = QLabel("Optional modules to enhance capabilities")
        info.setStyleSheet(f"color: {THEME['dim']}; font-size: 10px; padding: 5px;")
        layout.addWidget(info)
        
        # Get advanced modules
        advanced = tech_manager.active_config.get("advanced_modules", {})
        
        for category, modules in advanced.items():
            # Category label
            cat_label = QLabel(category.upper().replace("_", " "))
            cat_label.setStyleSheet(f"color: {THEME['accent']}; font-weight: bold; font-size: 11px; padding-top: 10px;")
            layout.addWidget(cat_label)
            
            for module_id, info in modules.items():
                module_frame = self._create_module_card(module_id, info)
                layout.addWidget(module_frame)
        
        layout.addStretch()
        return widget
    
    def _create_module_card(self, module_id: str, info: dict):
        """Create a card for an advanced module"""
        frame = QFrame()
        frame.setStyleSheet(f"background: {THEME['panel']}; border: 1px solid #333; border-radius: 4px; padding: 8px;")
        
        layout = QVBoxLayout(frame)
        layout.setSpacing(4)
        
        # Name
        name_label = QLabel(info.get("name", module_id))
        name_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        layout.addWidget(name_label)
        
        # Description
        desc = info.get("description", "")
        if desc:
            desc_label = QLabel(f"└ {desc}")
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet(f"color: {THEME['dim']}; font-size: 9px;")
            layout.addWidget(desc_label)
        
        # Status and Install button
        btn_layout = QHBoxLayout()
        
        status = info.get("status", "not_installed")
        status_label = QLabel(f"Status: {'⊗ NOT INSTALLED' if status == 'not_installed' else '✓ INSTALLED'}")
        status_label.setStyleSheet(f"font-size: 9px; font-family: 'Consolas';")
        btn_layout.addWidget(status_label)
        
        install_cmd = info.get("install_cmd", "")
        if install_cmd and status == "not_installed":
            install_btn = QPushButton("📦 Install")
            install_btn.setFixedWidth(80)
            install_btn.clicked.connect(lambda: self._install_module(module_id, install_cmd))
            btn_layout.addWidget(install_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        return frame
    
    def _install_module(self, module_id: str, install_cmd: str):
        """Show install command to user"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Install Command", 
                               f"To install {module_id}, run:\n\n{install_cmd}\n\nin your terminal")
    
    def _on_tech_changed(self, category: str, engine_id: str):
        """Called when user changes a technology"""
        self.pending_changes.append((category, engine_id))
    
    def _on_stack_changed(self, stack_name: str):
        """Called when user switches stack"""
        tech_manager.load_stack(stack_name)
        self.configuration_changed.emit()
        self.close()
        self.init_ui()  # Refresh UI
    
    def _save_stack(self):
        """Save current configuration as new stack"""
        # TODO: Open input dialog for stack name
        nervous_system.system("Save stack feature - TODO")
    
    def _apply_changes(self):
        """Apply all pending technology changes"""
        for category, engine_id in self.pending_changes:
            tech_manager.switch_engine(category, engine_id)
        
        self.pending_changes.clear()
        self.configuration_changed.emit()
        nervous_system.system("Configuration changes applied!")
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    panel = AdminPanel()
    panel.show()
    sys.exit(app.exec())
