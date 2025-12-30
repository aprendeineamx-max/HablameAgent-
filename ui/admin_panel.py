"""
Admin Panel - Technology Configuration Interface
Allows users to select and test different AI/automation technologies
"""
import sys
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QRadioButton, QButtonGroup,
                               QLineEdit, QFrame, QTabWidget, QWidget, QTextEdit,
                               QComboBox, QGroupBox, QScrollArea, QMessageBox, 
                               QProgressDialog)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from core.tech_manager import tech_manager
from core.logger import nervous_system


# --- MODERN DESIGN SYSTEM ---
THEME = {
    "surface0": "#0F172A",  # Main Canvas (Deep Slate)
    "surface1": "#1E293B",  # Cards/Panels
    "surface2": "#334155",  # Borders/Hover
    "accent": "#06B6D4",    # Cyan 500 (Primary Action)
    "accent_hover": "#22D3EE", 
    "secondary": "#8B5CF6", # Violet 500 (Highlights)
    "success": "#10B981",   # Emerald
    "error": "#EF4444",     # Red
    "text_main": "#F8FAFC", # White-ish
    "text_dim": "#94A3B8"   # Slate 400
}

STYLESHEET = f"""
QDialog {{
    background-color: {THEME['surface0']};
    color: {THEME['text_main']};
    font-family: 'Segoe UI', 'Inter', sans-serif;
}}

/* --- TABS --- */
QTabWidget::pane {{
    border: 1px solid {THEME['surface2']};
    background: {THEME['surface0']};
    border-radius: 8px;
    margin-top: -1px;
}}
QTabWidget::tab-bar {{
    left: 10px;
}}
QTabBar::tab {{
    background: {THEME['surface0']};
    color: {THEME['text_dim']};
    padding: 10px 20px;
    margin-right: 4px;
    border-bottom: 2px solid transparent;
    font-weight: bold;
    font-size: 13px;
}}
QTabBar::tab:selected {{
    color: {THEME['accent']};
    border-bottom: 2px solid {THEME['accent']};
}}
QTabBar::tab:hover {{
    color: {THEME['text_main']};
    background: {THEME['surface1']};
    border-radius: 4px;
}}

/* --- CARDS & GROUPS --- */
QGroupBox {{
    background-color: {THEME['surface1']};
    border: 1px solid {THEME['surface2']};
    border-radius: 12px;
    margin-top: 24px;
    padding-top: 24px;
    font-weight: bold;
    font-size: 12px;
    color: {THEME['accent']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 16px;
    top: 0px;
    padding: 0 8px;
    background-color: {THEME['surface1']}; 
    border-radius: 4px;
    color: {THEME['accent']};
}}

/* --- CONTROLS --- */
QRadioButton {{
    color: {THEME['text_main']};
    spacing: 10px;
    padding: 4px;
    font-size: 13px;
}}
QRadioButton::indicator {{
    width: 20px;
    height: 20px;
    border-radius: 10px;
    border: 2px solid {THEME['surface2']};
    background: transparent;
}}
QRadioButton::indicator:checked {{
    border: 2px solid {THEME['accent']};
    background: {THEME['accent']};
    image: none;
}}

QLineEdit, QComboBox {{
    background-color: {THEME['surface0']};
    border: 1px solid {THEME['surface2']};
    border-radius: 8px;
    padding: 10px;
    color: {THEME['text_main']};
    font-family: 'Consolas', monospace;
    font-size: 12px;
}}
QLineEdit:focus, QComboBox:focus {{
    border: 1px solid {THEME['accent']};
}}

/* --- BUTTONS --- */
QPushButton {{
    background-color: {THEME['surface2']};
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    color: {THEME['text_main']};
    font-weight: 600;
    font-size: 13px;
}}
QPushButton:hover {{
    background-color: {THEME['surface2']}88; /* Slightly lighter */
    border: 1px solid {THEME['accent']};
    color: {THEME['accent']};
}}
QPushButton:pressed {{
    background-color: {THEME['accent']};
    color: #000;
}}

/* Specialize Primary Button */
QPushButton#ApplyButton {{
    background-color: {THEME['accent']};
    color: #0F172A; /* Dark Text */
    font-size: 14px;
}}
QPushButton#ApplyButton:hover {{
    background-color: {THEME['accent_hover']};
    border: none;
}}

/* Specialize Test Button */
QPushButton#TestButton {{
    background-color: transparent;
    border: 1px solid {THEME['surface2']};
    padding: 6px 12px;
    font-size: 11px;
}}
QPushButton#TestButton:hover {{
    border-color: {THEME['success']};
    color: {THEME['success']};
}}

/* --- SCROLLBARS --- */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: {THEME['surface2']};
    min-height: 20px;
    border-radius: 4px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollArea {{
    background: transparent;
    border: none;
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
        """Create a modern card for an engine"""
        # Create Main Group
        group = QGroupBox(info.get("name", engine_id))
        
        # Determine Status Colors/Text
        status = info.get("status", "unknown")
        is_active = (engine_id == active_engine)
        
        # Main Layout
        layout = QVBoxLayout()
        layout.setSpacing(12)
        group.setLayout(layout)
        
        # Top Row: Radio + Status Badge
        top_row = QHBoxLayout()
        
        radio = QRadioButton("Enable Engine")
        radio.setProperty("engine_id", engine_id)
        if is_active:
            radio.setChecked(True)
        self.button_group.addButton(radio)
        radio.toggled.connect(lambda checked, eid=engine_id: 
                             self._on_engine_selected(eid) if checked else None)
        top_row.addWidget(radio)
        
        # Status Badge (Label with color)
        status_color = THEME.get(status, THEME['text_dim'])
        if status == "active": status_color = THEME['success']
        if status == "error": status_color = THEME['error']
        
        status_badge = QLabel(f"• {status.upper()}")
        status_badge.setStyleSheet(f"color: {status_color}; font-weight: bold; font-family: 'Consolas'; font-size: 11px;")
        top_row.addWidget(status_badge)
        top_row.addStretch()
        
        layout.addLayout(top_row)
        
        # Description (if active or expanded - currently always show description for clarity)
        desc_text = info.get("description", "")
        if desc_text:
            desc = QLabel(desc_text)
            desc.setWordWrap(True)
            desc.setStyleSheet(f"color: {THEME['text_dim']}; font-size: 11px; margin-left: 28px;")
            layout.addWidget(desc)

        # API Key / Error Area
        # If error, show red alert box
        if status == "error" and "error_msg" in info:
            err_frame = QFrame()
            err_frame.setStyleSheet(f"background: {THEME['error']}22; border-radius: 6px; padding: 8px;")
            err_layout = QHBoxLayout(err_frame)
            err_layout.setContentsMargins(8,4,8,4)
            
            err_lbl = QLabel(f"⚠ {info['error_msg']}")
            err_lbl.setStyleSheet(f"color: {THEME['error']}; font-size: 11px;")
            err_layout.addWidget(err_lbl)
            
            layout.addWidget(err_frame)
            
        # Key Input (only visible if requires key)
        if info.get("requires_key", False):
            key_frame = QFrame()
            key_frame.setStyleSheet(f"background: {THEME['surface0']}; border-radius: 6px; margin-left: 20px;")
            key_layout = QHBoxLayout(key_frame)
            key_layout.setContentsMargins(8,8,8,8)
            
            key_lbl = QLabel("API KEY:")
            key_lbl.setStyleSheet(f"color: {THEME['text_dim']}; font-size: 10px; font-weight: bold;")
            
            key_in = QLineEdit()
            key_in.setEchoMode(QLineEdit.Password)
            key_in.setPlaceholderText("••••••••••••••")
            key_in.setStyleSheet("border: none; background: transparent;")
            
            test_btn = QPushButton("Test")
            test_btn.setObjectName("TestButton")
            test_btn.setCursor(Qt.PointingHandCursor)
            test_btn.clicked.connect(lambda: self._test_engine(engine_id))
            
            key_layout.addWidget(key_lbl)
            key_layout.addWidget(key_in, 1)
            key_layout.addWidget(test_btn)
            
            layout.addWidget(key_frame)
            
        # Optional: Add dynamic controls if needed (like Voice Selection for Kokoro)
        if engine_id == "kokoro" and is_active:
             self._add_voice_selector(layout)

        return group

    def _add_voice_selector(self, parent_layout):
        """Add specific Kokoro controls"""
        try:
            from core.engines.tts.kokoro_engine import KokoroEngine
            # Just a quick check, ideally we use the instance from Voice but we can't import main instance easily
            # Use tech_manager to get options
            pass
            # For this refactor, we keep it simple. The previous code had it hardcoded in a specific block.
            # We will rely on user selecting Kokoro to triggering logic elsewhere if we want dynamic loading.
            # To keep this clean, I will recreate the voice selector logic here if feasible.
            
            # Re-implementing the simpler version:
            v_frame = QFrame()
            v_frame.setStyleSheet(f"margin-left: 20px; margin-top: 8px;")
            v_layout = QHBoxLayout(v_frame)
            v_layout.setContentsMargins(0,0,0,0)
            
            v_lbl = QLabel("Voice Model:")
            v_lbl.setStyleSheet(f"color: {THEME['text_dim']};")
            
            v_combo = QComboBox()
            # Hardcoded list for speed as per previous artifact
            opts = ["es_pe", "af_bella", "af_sarah", "am_adam", "am_michael", "bf_emma", "bf_isabella", "bm_george", "bm_lewis"]
            v_combo.addItems(opts)
            
            # Get current
            curr = tech_manager.get_engine_option("tts", "kokoro", "voice") or "es_pe"
            v_combo.setCurrentText(curr)
            
            v_combo.currentTextChanged.connect(lambda t: tech_manager.set_engine_option("tts", "kokoro", "voice", t))
            
            v_layout.addWidget(v_lbl)
            v_layout.addWidget(v_combo)
            v_layout.addStretch()
            
            parent_layout.addWidget(v_frame)
            
        except ImportError:
            pass
    
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
        header_frame = QFrame()
        header_frame.setStyleSheet("background: transparent; margin-bottom: 20px;")
        header_layout = QVBoxLayout(header_frame)
        
        title = QLabel("HABLAME // CORE")
        title.setFont(QFont("Segoe UI Black", 24))
        title.setStyleSheet(f"color: {THEME['text_main']}; letter-spacing: 2px;")
        
        subtitle = QLabel("AGI ORCHESTRATION & CONFIGURATION CONSOLE")
        subtitle.setFont(QFont("Segoe UI", 9, QFont.Bold))
        subtitle.setStyleSheet(f"color: {THEME['accent']}; letter-spacing: 4px;")
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header_frame)
        
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
        # Main container with ScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"background: {THEME['surface0']}; border: none;")
        
        container = QWidget()
        scroll.setWidget(container)
        
        layout = QVBoxLayout(container)
        
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
        return scroll
    
    def _create_module_card(self, module_id: str, info: dict):
        """Create a modern card for an advanced module"""
        frame = QFrame()
        # Card Style
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME['surface1']};
                border: 1px solid {THEME['surface2']};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(frame)
        layout.setSpacing(8)
        
        # Header Row: Name + Status Icon
        h_row = QHBoxLayout()
        name_label = QLabel(info.get("name", module_id))
        name_label.setStyleSheet("font-weight: 800; font-size: 13px; border: none; background: transparent;")
        
        status = info.get("status", "not_installed")
        status_icon = "✓" if status != "not_installed" else "⚪"
        status_color = THEME['success'] if status != "not_installed" else THEME['text_dim']
        
        stat_lbl = QLabel(status_icon)
        stat_lbl.setStyleSheet(f"color: {status_color}; font-size: 14px; font-weight: bold; border: none; background: transparent;")
        
        h_row.addWidget(name_label)
        h_row.addStretch()
        h_row.addWidget(stat_lbl)
        layout.addLayout(h_row)
        
        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"color: {THEME['surface2']}; border: none; background: {THEME['surface2']}; max-height: 1px;")
        layout.addWidget(line)
        
        # Description
        desc_text = info.get("description", "")
        desc = QLabel(desc_text)
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {THEME['text_dim']}; font-size: 11px; border: none; background: transparent;")
        layout.addWidget(desc)
        
        # Action Button (Install)
        install_cmd = info.get("install_cmd", "")
        if install_cmd and status == "not_installed":
            layout.addSpacing(8)
            install_btn = QPushButton("INSTALL MODULE")
            install_btn.setCursor(Qt.PointingHandCursor)
            install_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {THEME['surface2']};
                    color: {THEME['accent']};
                    font-size: 10px;
                    padding: 6px;
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    background-color: {THEME['accent']};
                    color: #000;
                }}
            """)
            install_btn.clicked.connect(lambda: self._install_module(module_id, install_cmd))
            layout.addWidget(install_btn)
        
        return frame
    
    def _install_module(self, module_id: str, install_cmd: str):
        """Run install command"""
        from PySide6.QtWidgets import QMessageBox, QProgressDialog
        from PySide6.QtCore import Qt
        import subprocess
        
        # Confirm
        reply = QMessageBox.question(self, "Install Module", 
                                    f"Do you want to run:\n{install_cmd}?",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # Show simple progress (blocking for now for simplicity, ideally async)
            progress = QProgressDialog(f"Installing {module_id}...", "Cancel", 0, 0, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            try:
                # Run command
                nervous_system.system(f"Installing {module_id}: {install_cmd}")
                
                # Use subprocess to run the command
                process = subprocess.Popen(
                    install_cmd, 
                    shell=True, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Wait for completion
                while process.poll() is None:
                    QApplication.processEvents()
                    if progress.wasCanceled():
                        process.terminate()
                        return
                
                stdout, stderr = process.communicate()
                
                progress.close()
                
                if process.returncode == 0:
                    QMessageBox.information(self, "Success", f"{module_id} installed successfully!")
                    # Update status in config
                    tech_manager.set_advanced_module_status(module_id, "active") 
                    # Refresh UI
                    self.close()
                    self.init_ui()
                else:
                    QMessageBox.critical(self, "Error", f"Installation failed:\n{stderr}")
                    
            except Exception as e:
                progress.close()
                QMessageBox.critical(self, "Error", f"Execution failed: {e}")
    
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
