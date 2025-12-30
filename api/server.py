
import os
import shutil
import tempfile
import traceback
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional

# Core Imports
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.voice import Voice
from core.brain import Brain
from core.action_engine import AutomationEngine
from core.logger import nervous_system
from core.tech_manager import tech_manager
from core.engines.stt.faster_whisper_engine import FasterWhisperEngine

# Initialize App
app = FastAPI(
    title="Hablame Nervous System API",
    description="Programmatic control for Hablame Agent",
    version="1.0.0"
)

# Initialize Components
try:
    nervous_system.system("API: Initializing Core Components...")
    voice = Voice()
    brain = Brain()
    hands = AutomationEngine()
except Exception as e:
    nervous_system.error("API", f"Init components failed: {e}")
    print(traceback.format_exc())

# STT Engine (Lazy load manually)
stt_engine = None

def get_stt_engine():
    global stt_engine
    if stt_engine is None:
        try:
            stt_engine = FasterWhisperEngine(model_size="base")
        except Exception as e:
            nervous_system.error("API", f"Failed to load FasterWhisper: {e}")
            raise HTTPException(status_code=500, detail="STT Engine unavailable")
    return stt_engine

# --- Data Models ---
class SpeakRequest(BaseModel):
    text: str

class ThinkRequest(BaseModel):
    prompt: str

class CommandRequest(BaseModel):
    command: str

# --- Endpoints ---

@app.get("/")
def health_check():
    return {"status": "online", "message": "Hablame API is running"}

@app.get("/v1/system/status")
def get_system_status():
    """Get current technology stack status"""
    return tech_manager.active_config

@app.post("/v1/tts/speak")
def speak(request: SpeakRequest):
    """Make the agent speak"""
    try:
        voice.speak(request.text)
        return {"status": "success", "message": f"Spoke: {request.text}"}
    except Exception as e:
        nervous_system.error("API", f"Speak Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/llm/think")
def think(request: ThinkRequest):
    """Ask the LLM a question"""
    try:
        response = brain.think(request.prompt)
        return {"response": response}
    except Exception as e:
        nervous_system.error("API", f"Think Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/action/execute")
def execute_command(request: CommandRequest):
    """Execute a natural language command (Brain -> Motor)"""
    try:
        # 1. Think (Getting the plan)
        nervous_system.system(f"API Command received: {request.command}")
        action_plan = brain.think(request.command)
        
        # 2. Check if valid plan
        if not action_plan or action_plan.get("action") == "error":
             return {"status": "error", "message": "Brain could not understand command"}
             
        # 3. Execute (Motor or Chat)
        action_type = action_plan.get("action")
        
        if action_type in ["chat", "clarify"]:
            # API Mode: Just return the text, don't necessarily speak on server (optional)
            # Or we can speak if we want server to speak. Let's speak for consistency.
            # But primarily return execution success.
            params = action_plan.get("parameters", {})
            text_response = params.get("text") or params.get("question")
            
            # Speak on server (if desired) or just log
            nervous_system.vocal(f"API Chat Response: {text_response}")
            # Try to speak if voice is available module-side (might conflict with main app if running)
            # For now, just mark as success.
            
            return {
                "status": "success",
                "plan": action_plan,
                "executed": True,
                "response_text": text_response
            }
            
        else:
            # Physical Action
            success = hands.execute_task(action_plan)
            
            return {
                "status": "success" if success else "failed",
                "plan": action_plan,
                "executed": success
            }
    except Exception as e:
        error_msg = traceback.format_exc()
        nervous_system.error("API", f"CRITICAL 500 EXECUTE: {error_msg}")
        print(f"CRITICAL API ERROR: {error_msg}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/stt/transcribe")
def transcribe_audio(file: UploadFile = File(...)):
    """Transcribe an audio file"""
    try:
        # Save upload to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        
        # Transcribe
        engine = get_stt_engine()
        segments, info = engine.model.transcribe(tmp_path, beam_size=5)
        text = " ".join([segment.text for segment in segments])
        
        # Cleanup
        os.remove(tmp_path)
        
        return {"text": text, "language": info.language, "probability": info.language_probability}
        
    except Exception as e:
        nervous_system.error("API", f"Transcribe Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
