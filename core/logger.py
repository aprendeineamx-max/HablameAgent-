import logging
import sys
from colorama import Fore, Style, init

# Inicializar colorama para Windows
init(autoreset=True)

class SupremeLogger:
    def __init__(self):
        self.logger = logging.getLogger("HablameNervousSystem")
        self.logger.setLevel(logging.DEBUG)
        
        # UI Callback for real-time display
        self.ui_callback = None
        
        # Formato de archivo (Detallado)
        file_handler = logging.FileHandler("nervous_system.log", mode='w', encoding='utf-8')
        file_formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s')
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Handler de Consola (Visualmente rico pero limpio)
        # No usamos el default handler para tener control total de colores
        self.console_handler = logging.StreamHandler(sys.stdout)
        self.console_handler.setLevel(logging.INFO)

    def set_ui_callback(self, callback):
        """Set callback function for UI log display"""
        self.ui_callback = callback

    def _log(self, level, area, message, color=Fore.WHITE):
        """
        Log centralizado con metáforas biológicas.
        Areas: SENSORY, COGNITIVE, MOTOR, VOCAL, SYSTEM
        """
        icon_map = {
            "SENSORY": "👂",
            "COGNITIVE": "🧠",
            "MOTOR": "✋",
            "VOCAL": "🗣️",
            "SYSTEM": "💻"
        }
        icon = icon_map.get(area, "•")
        
        # Consola: Visual
        console_msg = f"{color}{Style.BRIGHT}[{area}] {icon} {message}{Style.RESET_ALL}"
        print(console_msg)
        
        # UI Callback (if set)
        if self.ui_callback:
            try:
                ui_msg = f"[{area}] {icon} {message}"
                self.ui_callback(ui_msg)
            except Exception:
                pass  # Don't crash if UI callback fails
        
        # Archivo: Estructurado
        if level == "INFO":
            self.logger.info(f"[{area}] {message}")
        elif level == "ERROR":
            self.logger.error(f"[{area}] {message}")
        elif level == "DEBUG":
            self.logger.debug(f"[{area}] {message}")

    def sensory(self, message):
        self._log("INFO", "SENSORY", message, Fore.CYAN)

    def cognitive(self, message):
        self._log("INFO", "COGNITIVE", message, Fore.MAGENTA)

    def motor(self, message):
        self._log("INFO", "MOTOR", message, Fore.YELLOW)
    
    def vocal(self, message):
        self._log("INFO", "VOCAL", message, Fore.GREEN)

    def system(self, message):
        self._log("INFO", "SYSTEM", message, Fore.BLUE)

    def error(self, area, message):
        self._log("ERROR", area, f"FAILURE: {message}", Fore.RED)

# Instancia global
nervous_system = SupremeLogger()
