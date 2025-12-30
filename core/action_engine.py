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
        # Typing humanizado para evitar detección de bots en algunos sitios
        nervous_system.motor(f"Escribiendo texto: '{text}'")
        pyautogui.write(text, interval=0.01)
        return True

    def _do_press_key(self, params):
        keys = params.get("key", "").split('+')
        clean_keys = [k.strip().lower() for k in keys]
        nervous_system.motor(f"Simulando pulsación: {clean_keys}")
        pyautogui.hotkey(*clean_keys)
        return True

    def _do_click(self, params):
        target_name = params.get("element", "")
        nervous_system.motor(f"Escaneando entorno visual buscando: '{target_name}'...")
        
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
        best_match = self._fuzzy_find_recursive(window, target_name, max_depth=10) # Profundidad 10 es bastante
        
        if best_match:
            nervous_system.motor(f"Objetivo encontrado (Fuzzy Logic): '{best_match.Name}'")
            self._click_element(best_match)
            return True
        
        nervous_system.error("MOTOR", f"Objetivo '{target_name}' no encontrado en el árbol visual actual.")
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
        
        # Algoritmo de Walker para recorrer el árbol
        walker = auto.TreeWalker(auto.Condition.TrueCondition)
        element = walker.GetFirstChildElement(root_control)
        
        # Nota: Python recursion puede ser lenta/topear stack, 
        # para depth 10 en UI Tree es mejor iterativo o limitado.
        # Por simplicidad y potencia haremos una búsqueda plana de todos los descendientes
        # usando la feature de FindAll de UIA que es C++ native (rápida).
        
        try:
            # Obtenemos TODOS los elementos (botones, textos, items)
            # Cuidado: Esto puede ser lento en ventanas gigantes (como Word lleno)
            # all_elements = root_control.GetChildren() + root_control.GetChildren() # Esto solo da hijos directos
            
            # Mejor approach: Usar FindAll con Depth
            # Optimization: Solo buscar tipos clickeables
            conditions = auto.OrCondition(
                auto.ControlTypeCondition(auto.ControlType.ButtonControl),
                auto.ControlTypeCondition(auto.ControlType.MenuItemControl),
                auto.ControlTypeCondition(auto.ControlType.TextControl), # A veces los botones son texto
                auto.ControlTypeCondition(auto.ControlType.TabItemControl),
                auto.ControlTypeCondition(auto.ControlType.HyperlinkControl)
            )
            
            # Limitamos el scope si es muy grande, pero usuario pidió POTENCIA
            matches = root_control.FindAll(auto.TreeScope.Descendants, conditions)
            
            target_lower = target_text.lower()
            
            for el in matches:
                name = el.Name
                if not name: continue
                
                name_lower = name.lower()
                
                # Match Exacto Contenido
                if target_lower == name_lower:
                    return el
                
                # Match Parcial ("Guardar" in "Guardar Todo")
                if target_lower in name_lower:
                    # Damos prioridad a strings cortos (más exactos)
                    ratio = 0.9 if len(name_lower) < len(target_lower)*2 else 0.7
                    if ratio > best_ratio:
                        best_ratio = ratio
                        best_control = el
                    continue
                
                # Fuzzy (Levenshtein)
                ratio = difflib.SequenceMatcher(None, target_lower, name_lower).ratio()
                if ratio > best_ratio and ratio > 0.6: # Umbral de confianza
                    best_ratio = ratio
                    best_control = el

            return best_control

        except Exception as e:
            nervous_system.error("MOTOR", f"Error en escaneo profundo: {e}")
            return None

if __name__ == "__main__":
    engine = AutomationEngine()
    # Test Fuzzy
    # engine.execute_task({"action": "click", "parameters": {"element": "File"}})
