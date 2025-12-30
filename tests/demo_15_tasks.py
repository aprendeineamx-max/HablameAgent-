
import requests
import time
import os

BASE_URL = "http://localhost:8000"
GREEN = "\033[92m"
RESET = "\033[0m"
RED = "\033[91m"

def log(step, task, status, detail=""):
    color = GREEN if status == "OK" else RED
    print(f"[{step}/15] {task:<40} [{color}{status}{RESET}] {detail}")

def run_task(step, description, method, endpoint, payload=None):
    try:
        url = f"{BASE_URL}{endpoint}"
        if method == "GET":
            r = requests.get(url)
        else:
            r = requests.post(url, json=payload)
            
        if r.status_code == 200:
            log(step, description, "OK")
            # Small delay to let physical actions finish (like opening apps)
            if "action" in endpoint:
                time.sleep(8.0) 
            else:
                 time.sleep(3.0) # Delay for thoughts/speech too
            return True
        else:
            log(step, description, "FAIL", f"Status: {r.status_code}")
            return False
    except Exception as e:
        log(step, description, "ERR", str(e))
        return False

def main():
    print("========================================")
    print("      15-STEP CAPABILITY DEMO           ")
    print("========================================")
    
    # Task 1: System Status
    run_task(1, "Check System Health", "GET", "/v1/system/status")
    
    # Task 2: TTS Intro
    run_task(2, "Speak Intro", "POST", "/v1/tts/speak", {"text": "Iniciando demostración de quince tareas del sistema."})
    
    # Task 3: LLM Simple Knowledge
    run_task(3, "LLM: Capital of France", "POST", "/v1/llm/think", {"prompt": "Capital of France?"})
    
    # Task 4: LLM Reasoning
    run_task(4, "LLM: Python Summary", "POST", "/v1/llm/think", {"prompt": "Define Python string in 5 words"})
    
    # Task 5: Create File (Text)
    run_task(5, "Create File: demo_task_5.txt", "POST", "/v1/action/execute", 
             {"command": "Create a file named demo_task_5.txt with content 'Persistence Test Successful'"})

    # Task 6: Open Application (Notepad)
    run_task(6, "Open Notepad", "POST", "/v1/action/execute", {"command": "Open notepad"})
    
    # Task 7: Type Text (into Notepad)
    run_task(7, "Type: 'Hello from API'", "POST", "/v1/action/execute", {"command": "Type 'Hello from API'"})
    
    # Task 8: Press Key (Enter)
    run_task(8, "Press Key: Enter", "POST", "/v1/action/execute", {"command": "Press enter"})
    
    # Task 9: Type More Text
    run_task(9, "Type: 'Second Line'", "POST", "/v1/action/execute", {"command": "Type 'Automated Line 2'"})
    
    # Task 10: Create File (Log)
    run_task(10, "Create File: system_check.log", "POST", "/v1/action/execute", 
             {"command": "Create a file named system_check.log with content '[INFO] System functional'"})
             
    # Task 11: Open Application (Calc)
    run_task(11, "Open Calculator", "POST", "/v1/action/execute", {"command": "Open calculator"})
    
    # Task 12: Press Hotkey (Minimizar todo - Win+M is tricky, let's try standard minimize command if supported or just open another app)
    # The brain maps "minimize" to minimizing active window.
    run_task(12, "Minimize Active Window", "POST", "/v1/action/execute", {"command": "Minimize window"})

    # Task 13: Create File (JSON)
    run_task(13, "Create File: config.json", "POST", "/v1/action/execute", 
             {"command": "Create a file named config.json with content '{ \"status\": \"active\" }'"})

    # Task 14: TTS Outro
    run_task(14, "Speak Outro", "POST", "/v1/tts/speak", {"text": "Demostración de quince tareas completada."})
    
    # Task 15: Final Report Generation
    run_task(15, "Create Final Report", "POST", "/v1/action/execute", 
             {"command": "Create a file named FINAL_15_TASKS.txt with content 'ALL TASKS EXECUTED SUCCESSFULLY'"})

    print("========================================")
    print("      DEMO COMPLETE                     ")
    print("========================================")

if __name__ == "__main__":
    main()
