import uiautomation as auto
import subprocess
import time
import os
import pyautogui
import difflib
from core.config import settings
from core.logger import nervous_system

# Aumentamos el timeout para búsquedas profundas si es necesario
auto.SetGlobalSearchTimeout(5) 

class AutomationEngine:
    def __init__(self):
        nervous_system.motor("Cortex Motor (Precision Mode) Inicializado.")
        self.width, self.height = pyautogui.size()

    def execute_task(self, task_data):
        """
        Ejecuta acciones con validación de errores.
        """
        action = task_data.get("action", "").lower()
        params = task_data.get("parameters", {})
        
        nervous_system.motor(f"Impulso Recibido: {action} | Datos: {params}")

        if action == "chain":
            steps = params.get("steps", [])
            for step in steps:
                if not self.execute_task(step):
                    nervous_system.error("MOTOR", f"Cadena rota en paso: {step}")
                    return False # Romper cadena si un paso falla (Seguridad)
            return True

        method_name = f"_do_{action}"
        if hasattr(self, method_name):
            try:
                method = getattr(self, method_name)
                return method(params)
            except Exception as e:
                nervous_system.error("MOTOR", f"CRITICAL ERROR en {action}: {e}")
                return False
        else:
            nervous_system.error("MOTOR", f"Acción desconocida: {action}")
            return False

    # --- ACCIONES PRINCIPALES ---

    def _do_open_app(self, params):
        app_name = params.get("app_name", "").lower()
        nervous_system.motor(f"Intentando ejecutar proceso: {app_name}")
        
        # Mapeo extendido
        apps = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "chrome": "chrome.exe",
            "edge": "msedge.exe",
            "cmd": "cmd.exe",
            "explorer": "explorer.exe",
            "spotify": "spotify.exe",
            "code": "code",
            "word": "winword.exe",
            "excel": "excel.exe",
            "powerpoint": "powerpnt.exe"
        }
        
        cmd = apps.get(app_name, app_name)
        try:
            # Opción 1: App Switcher (Si ya está abierta, traer al frente)
            # Esto evita abrir 50 Chrome Tabs
            # (Simplificado para esta versión, usaríamos pygetwindow para esto)
            
            subprocess.Popen(cmd, shell=True)
            time.sleep(3) # Damos tiempo al sistema
            nervous_system.motor(f"Proceso lanzado: {cmd}")
            return True
        except Exception as e:
            nervous_system.error("MOTOR", f"Fallo al abrir {app_name}: {e}")
            return False

    def _do_type(self, params):
        text = params.get("text", "")
        nervous_system.motor(f"Escribiendo texto: '{text}'")
        
        try:
            # Use clipboard method (more reliable for special characters)
            import pyperclip
            pyperclip.copy(text)
            time.sleep(0.1)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.2)
            return True
        except ImportError:
            # Fallback to direct typing if pyperclip not available
            nervous_system.motor("Pyperclip no disponible, usando método directo...")
            for char in text:
                pyautogui.press(char)
                time.sleep(0.01)
            return True
        except Exception as e:
            nervous_system.error("MOTOR", f"Error al escribir: {e}")
            return False

    def _do_press_key(self, params):
        keys = params.get("key", "").split('+')
        clean_keys = [k.strip().lower() for k in keys]
        nervous_system.motor(f"Simulando pulsación: {clean_keys}")
        try:
            pyautogui.hotkey(*clean_keys)
            time.sleep(0.3)  # Wait for action to complete
            return True
        except Exception as e:
            nervous_system.error("MOTOR", f"Error en hotkey: {e}")
            return False

    def _do_create_file(self, params):
        """Creates a file with specific content (OS Level)"""
        path = params.get("path", "")
        content = params.get("content", "")
        
        if not path:
             nervous_system.error("MOTOR", "Falta ruta para crear archivo")
             return False
             
        nervous_system.motor(f"Creando archivo: {path}")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            nervous_system.motor("✓ Archivo creado exitosamente")
            return True
        except Exception as e:
            nervous_system.error("MOTOR", f"Error creando archivo: {e}")
            return False

    def _do_click(self, params):
        target_name = params.get("element", "")
        nervous_system.motor(f"Escaneando entorno visual buscando: '{target_name}'...")
        
        # Check for keyboard shortcuts as smart fallback FIRST
        shortcut = self._get_keyboard_shortcut(target_name)
        if shortcut:
            nervous_system.motor(f"Usando atajo de teclado inteligente: {shortcut}")
            return self._do_press_key({"key": shortcut})
        
        window = auto.GetForegroundControl()
        if not window:
            nervous_system.error("MOTOR", "No hay ventana activa (Ceguera temporal).")
            return False

        # 1. Búsqueda Directa (Rápida)
        found = window.Control(Name=target_name, searchDepth=3)
        if found.Exists():
            nervous_system.motor("Objetivo encontrado (Visual Directo).")
            self._click_element(found)
            return True

        # 2. Búsqueda Profunda + Fuzzy (Lenta pero Poderosa)
        nervous_system.motor("Objetivo no visible. Iniciando Escaneo Profundo (Deep Scan)...")
        best_match = self._fuzzy_find_recursive(window, target_name, max_depth=10)
        
        if best_match:
            nervous_system.motor(f"Objetivo encontrado (Fuzzy Logic): '{best_match.Name}'")
            self._click_element(best_match)
            return True
        
        nervous_system.error("MOTOR", f"Objetivo '{target_name}' no encontrado. Smart fallback no disponible.")
        return False

    # --- UTILIDADES DE PRECISIÓN ---

    def _click_element(self, element):
        """
        Realiza un clic seguro. 
        Mueve el mouse visualmente hacia el objetivo antes de hacer clic (Feedback visual).
        """
        rect = element.BoundingRectangle
        if rect:
            center_x = (rect.left + rect.right) // 2
            center_y = (rect.top + rect.bottom) // 2
            
            # Movimiento humano
            nervous_system.motor(f"Moviendo extremidad a: ({center_x}, {center_y})")
            pyautogui.moveTo(center_x, center_y, duration=0.3)
            # Clic UIA (más robusto que pyautogui click)
            element.Click()
        else:
            # Fallback si no tiene rect (raro)
            nervous_system.motor("Clic ciego (sin coordenadas visuales).")
            element.Click()

    def _fuzzy_find_recursive(self, root_control, target_text, max_depth=5):
        """
        Recorre el árbol de UI y busca el mejor match de texto.
        Devuelve el Control si la similitud > 0.8
        """
        best_control = None
        best_ratio = 0.0
        
        try:
            # FIXED: TreeWalker no existe en uiautomation 2.0.29
            # Usamos FindAll directamente que es más eficiente
            
            # Optimization: Solo buscar tipos clickeables
            conditions = auto.OrCondition(
                auto.ControlTypeCondition(auto.ControlType.ButtonControl),
                auto.ControlTypeCondition(auto.ControlType.MenuItemControl),
                auto.ControlTypeCondition(auto.ControlType.TextControl),
                auto.ControlTypeCondition(auto.ControlType.TabItemControl),
                auto.ControlTypeCondition(auto.ControlType.HyperlinkControl)
            )
            
            # Buscar en todos los descendientes
            matches = root_control.FindAll(auto.TreeScope.Descendants, conditions)
            
            target_lower = target_text.lower()
            
            for el in matches:
                name = el.Name
                if not name: continue
                
                name_lower = name.lower()
                
                # Match Exacto
                if target_lower == name_lower:
                    return el
                
                # Match Parcial ("Guardar" in "Guardar Todo")
                if target_lower in name_lower:
                    ratio = 0.9 if len(name_lower) < len(target_lower)*2 else 0.7
                    if ratio > best_ratio:
                        best_ratio = ratio
                        best_control = el
                    continue
                
                # Fuzzy (Levenshtein)
                ratio = difflib.SequenceMatcher(None, target_lower, name_lower).ratio()
                if ratio > best_ratio and ratio > 0.6:
                    best_ratio = ratio
                    best_control = el

            return best_control

        except Exception as e:
            nervous_system.error("MOTOR", f"Error en escaneo profundo: {e}")
            return None
    
    def _get_keyboard_shortcut(self, target_text: str) -> str:
        """
        Smart keyboard shortcut mapping for common actions
        Returns keyboard shortcut if target matches known patterns
        """
        target_lower = target_text.lower().strip()
        
        # File operations (common across most apps)
        shortcuts = {
            # File menu
            "guardar": "ctrl+s",
            "save": "ctrl+s",
            "abrir": "ctrl+o",
            "open": "ctrl+o",
            "nuevo": "ctrl+n",
            "new": "ctrl+n",
            "cerrar": "ctrl+w",
            "close": "ctrl+w",
            "imprimir": "ctrl+p",
            "print": "ctrl+p",
            
            # Edit menu
            "copiar": "ctrl+c",
            "copy": "ctrl+c",
            "pegar": "ctrl+v",
            "paste": "ctrl+v",
            "cortar": "ctrl+x",
            "cut": "ctrl+x",
            "deshacer": "ctrl+z",
            "undo": "ctrl+z",
            "rehacer": "ctrl+y",
            "redo": "ctrl+y",
            "buscar": "ctrl+f",
            "find": "ctrl+f",
            
            # Window operations
            "minimizar": "win+down",
            "minimize": "win+down",
            "maximizar": "win+up",
            "maximize": "win+up",
            
            # Browser
            "actualizar": "f5",
            "refresh": "f5",
            "nueva pestaña": "ctrl+t",
            "new tab": "ctrl+t",
            "cerrar pestaña": "ctrl+w",
            "close tab": "ctrl+w",
            
            # System
            "escritorio": "win+d",
            "desktop": "win+d",
            "explorador": "win+e",
            "explorer": "win+e"
        }
        
        return shortcuts.get(target_lower, None)
    
    # --- NEW WINDOW MANAGEMENT COMMANDS ---
    
    def _do_minimize(self, params):
        """Minimize current window"""
        nervous_system.motor("Minimizando ventana activa...")
        pyautogui.hotkey('win', 'down')
        return True
    
    def _do_maximize(self, params):
        """Maximize current window"""
        nervous_system.motor("Maximizando ventana activa...")
        pyautogui.hotkey('win', 'up')
        return True
    
    def _do_close_window(self, params):
        """Close current window"""
        nervous_system.motor("Cerrando ventana activa...")
        pyautogui.hotkey('alt', 'f4')
        return True
    
    def _do_save(self, params):
        """Universal save command"""
        nervous_system.motor("Guardando documento (Ctrl+S)...")
        pyautogui.hotkey('ctrl', 's')
        time.sleep(0.5)
        return True
    
    def _do_refresh(self, params):
        """Refresh/Reload"""
        nervous_system.motor("Actualizando (F5)...")
        pyautogui.press('f5')
        return True
    
    def _do_screenshot(self, params):
        """Take screenshot"""
        nervous_system.motor("Capturando pantalla...")
        pyautogui.hotkey('win', 'shift', 's')  # Windows Snipping Tool
        return True
    
    def _do_switch_app(self, params):
        """Switch between applications (Alt+Tab)"""
        nervous_system.motor("Cambiando de aplicación...")
        pyautogui.hotkey('alt', 'tab')
        time.sleep(0.5)
        return True

if __name__ == "__main__":
    engine = AutomationEngine()
    # Test
    # engine.execute_task({"action": "save", "parameters": {}})
