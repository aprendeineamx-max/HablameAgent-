
import requests
import time
import os

BASE_URL = "http://localhost:8000"
TEST_FILE_NAME = "ai_poem.txt"
TEST_FILE_PATH = os.path.abspath(TEST_FILE_NAME)

def test_status():
    print("\n[TEST 1] System Status Connectivity")
    try:
        r = requests.get(f"{BASE_URL}/v1/system/status")
        if r.status_code == 200:
            print(f"✓ Host Online. Stack: {r.json().get('active_stack')}")
        else:
            print(f"FAILED: {r.status_code}")
    except Exception as e:
        print(f"ERROR: {e}")

def test_complex_chain():
    print("\n[TEST 2] Complex Chain (OS File Creation + App Opening)")
    
    # Clean previous
    if os.path.exists(TEST_FILE_PATH):
        os.remove(TEST_FILE_PATH)
        
    # Command that forces a CHAIN: "Create this file AND THEN open notepad"
    # The updated Brain prompt should map "Create file" -> create_file (OS) and "Open notepad" -> open_app
    poem = "Silicon dreams in wires deep, awakening while the humans sleep."
    command = f"Create a file named {TEST_FILE_NAME} containing the text '{poem}' and then open notepad."
    
    print(f"Sending Command: '{command}'")
    
    try:
        data = {"command": command}
        r = requests.post(f"{BASE_URL}/v1/action/execute", json=data)
        
        if r.status_code == 200:
            res = r.json()
            print(f"✓ Execution Response: {res.get('status')}")
            
            # Verify File Existence (OS Check)
            if os.path.exists(TEST_FILE_PATH):
                print(f"✓ VERIFIED: File '{TEST_FILE_NAME}' exists on disk.")
                with open(TEST_FILE_PATH, 'r') as f:
                    content = f.read()
                print(f"  Content: {content}")
                if poem in content:
                     print("  Content Match: YES")
                else:
                     print("  Content Match: NO (Partial Content?)")
            else:
                print("❌ FAILED: File was not created on disk.")
                
            # Verify Notepad (Visual check for user)
            print("✓ CHECK: Notepad should be open on screen now.")
            
        else:
            print(f"FAILED Execute: {r.status_code} - {r.text}")
            
    except Exception as e:
        print(f"ERROR: {e}")

def main():
    print("========================================")
    print("      HABLAME ADVANCED INTEGRITY        ")
    print("========================================")
    test_status()
    time.sleep(1)
    test_complex_chain()
    print("\n========================================")

if __name__ == "__main__":
    main()
