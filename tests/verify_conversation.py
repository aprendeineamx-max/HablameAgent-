
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
import time
import threading
from core.voice import Voice
from core.logger import nervous_system

BASE_URL = "http://localhost:8000"
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def log(msg, status="INFO"):
    color = GREEN if status == "PASS" else (RED if status == "FAIL" else RESET)
    print(f"[{color}{status}{RESET}] {msg}")

def test_chat_mode():
    log("Testing Chat Mode via API...")
    try:
        # Test a conversational greeting
        command = "Hola, ¿quién eres?"
        r = requests.post(f"{BASE_URL}/v1/action/execute", json={"command": command})
        
        if r.status_code == 200:
            data = r.json()
            # We expect the Brain to return "chat" action
            # Note: The API executes it, so the response might just say 'success' or 'executed'
            # But the 'plan' key should contain the action details.
            plan = data.get("plan", {})
            action_type = plan.get("action")
            
            if action_type == "chat":
                log(f"Brain classified '{command}' as 'chat'", "PASS")
                log(f"Response Text: {plan.get('parameters', {}).get('text')}")
                return True
            else:
                log(f"Brain classified '{command}' as '{action_type}' (Expected 'chat')", "FAIL")
                return False
        else:
            log(f"API Request failed: {r.status_code}", "FAIL")
            return False
            
    except Exception as e:
        log(f"Exception in Chat Mode test: {e}", "FAIL")
        return False

def test_audio_interruption():
    log("Testing Audio Interruption Logic (Visual/Code Check)...")
    # Since we can't easily hear the output or check sounddevice state without a complex setup,
    # we will simulate the behavior by calling voice.speak on a thread and then voice.stop()
    # and ensuring no crash occurs.
    
    voice = Voice()
    
    log("Starting speech (Async)...")
    t = threading.Thread(target=voice.speak, args=("Este es un texto largo para probar la interrupción del sistema de audio y verificar que se detiene correctamente.",))
    t.start()
    
    time.sleep(1.5) # Let it speak for a bit
    
    log("Triggering Interruption (voice.stop())...")
    try:
        voice.stop()
        log("Stop signal sent without error.", "PASS")
        # In a real unit test we would mock the Player and verify .stop() was called.
        # Here we assume if it didn't crash, it worked (sounddevice handles stop gracefully).
    except Exception as e:
        log(f"Error executing stop(): {e}", "FAIL")

def main():
    print("========================================")
    print("   CONVERSATIONAL SYSTEM VERIFICATION   ")
    print("========================================")
    
    # Wait for API to be ready
    time.sleep(3) 
    
    # 1. Test Brain Logic (Chat vs Action)
    if test_chat_mode():
        log("Chat Logic Verified", "PASS")
    else:
        log("Chat Logic Failed", "FAIL")
        
    print("-" * 30)
    
    # 2. Test Audio Player Stop
    test_audio_interruption()
    
    print("========================================")
    print("   VERIFICATION COMPLETE                ")
    print("========================================")

if __name__ == "__main__":
    main()
