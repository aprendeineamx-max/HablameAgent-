
import os
import sys
import requests
import json
import time

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

class SystemVerifier:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.report = []
        self.failed_tests = 0

    def log(self, message, status="INFO"):
        if status == "PASS":
            print(f"[{GREEN}PASS{RESET}] {message}")
            self.report.append(f"[PASS] {message}")
        elif status == "FAIL":
            print(f"[{RED}FAIL{RESET}] {message}")
            self.report.append(f"[FAIL] {message}")
            self.failed_tests += 1
        else:
            print(f"[INFO] {message}")

    def check_file(self, path, name):
        if os.path.exists(path):
            self.log(f"File found: {name}", "PASS")
        else:
            self.log(f"File MISSING: {name} ({path})", "FAIL")

    def run_api_check(self):
        self.log("Converting with Nervous System API...")
        try:
            r = requests.get(f"{self.base_url}/v1/system/status")
            if r.status_code == 200:
                self.log("API connectivity established", "PASS")
                data = r.json()
                active_stack = data.get("active_stack", {})
                self.log(f"Active Stack: {active_stack}")
            else:
                self.log(f"API returned {r.status_code}", "FAIL")
        except:
             self.log("API Server unreachable. check RUN_API.bat", "FAIL")

    def run_audio_check(self):
        # 1. Check Kokoro Model
        self.check_file("kokoro/kokoro-v0_19.onnx", "Kokoro Model")
        self.check_file("kokoro/voices-v1.0.bin", "Kokoro Voices")

        # 2. Check Action Engine (create file)
        self.log("Testing Action Engine (File Creation via API)...")
        filename = "SYSTEM_VERIFIED.txt"
        abspath = os.path.abspath(filename)
        if os.path.exists(abspath): os.remove(abspath)
        
        try:
            cmd = f"Create a file named {filename} with the content: SYSTEM_INTEGRITY_CONFIRMED"
            r = requests.post(f"{self.base_url}/v1/action/execute", json={"command": cmd})
            if r.status_code == 200 and os.path.exists(abspath):
                self.log("ActionEngine: File Creation (Brain->Motor)", "PASS")
            else:
                self.log(f"ActionEngine Failed. Status: {r.status_code}", "FAIL")
        except:
            self.log("ActionEngine API call failed", "FAIL")

    def generate_report(self):
        print("\n" + "="*40)
        print("   HABLAME FINAL DIAGNOSTIC REPORT")
        print("="*40)
        for line in self.report:
            print(line)
        print("-"*40)
        
        result_file = "DIAGNOSTIC_RESULT.txt"
        with open(result_file, "w") as f:
            f.write("\n".join(self.report))
            
        if self.failed_tests == 0:
            print(f"\n{GREEN}RESULT: SYSTEM OPERATIONAL{RESET}")
            return True
        else:
            print(f"\n{RED}RESULT: SYSTEM UNSTABLE ({self.failed_tests} failures){RESET}")
            return False

if __name__ == "__main__":
    verifier = SystemVerifier()
    verifier.run_api_check()
    verifier.run_audio_check()
    verifier.generate_report()
