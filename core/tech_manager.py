"""
Technology Manager - Central hub for managing all AI/automation technologies
Allows hot-swapping between different engines without restart
"""
import json
import os
from pathlib import Path
from typing import Dict, Tuple, Optional, Any
from core.logger import nervous_system


class TechnologyManager:
    """
    Manages all available technologies and their configurations.
    Provides unified interface for switching between STT, TTS, LLM, and Motor engines.
    """
    
    def __init__(self):
        self.config_dir = Path(__file__).parent.parent / "configs"
        self.config_file = self.config_dir / "tech_stack.json"
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
        
        # Load or create default config
        self.active_config = self._load_config()
        
        nervous_system.system("Technology Manager initialized")
    
    def _load_config(self) -> Dict:
        """Load configuration from file or create default"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                nervous_system.error("SYSTEM", f"Error loading config: {e}")
                return self._get_default_config()
        else:
            config = self._get_default_config()
            self._save_config(config)
            return config
    
    def _get_default_config(self) -> Dict:
        """Get default configuration with working technologies"""
        return {
            "active_stack": "default",
            "stacks": {
                "default": {
                    "stt": "google_stt",
                    "tts": "pyttsx3",
                    "llm": "sambanova",
                    "motor": "uiautomation"
                },
                "premium": {
                    "stt": "hf_whisper",
                    "tts": "elevenlabs",
                    "llm": "sambanova",
                    "motor": "uiautomation"
                },
                "local_only": {
                    "stt": "local_whisper",
                    "tts": "pyttsx3",
                    "llm": "local_llama",
                    "motor": "uiautomation"
                }
            },
            "technologies": {
                "stt": {
                    "google_stt": {
                        "name": "Google Speech-to-Text",
                        "status": "active",
                        "requires_key": False,
                        "free": True
                    },
                    "hf_whisper": {
                        "name": "HuggingFace Whisper v3",
                        "status": "error",
                        "requires_key": True,
                        "free": True,
                        "error_msg": "410 API Error"
                    }
                },
                "tts": {
                    "pyttsx3": {
                        "name": "Local TTS (pyttsx3)",
                        "status": "active",
                        "requires_key": False,
                        "free": True
                    },
                    "elevenlabs": {
                        "name": "ElevenLabs",
                        "status": "error",
                        "requires_key": True,
                        "free": False,
                        "error_msg": "401 Free Tier Blocked"
                    }
                },
                "llm": {
                    "sambanova": {
                        "name": "SambaNova (Llama 3.3 70B)",
                        "status": "active",
                        "requires_key": True,
                        "free": True
                    }
                },
                "motor": {
                    "uiautomation": {
                        "name": "UIAutomation + PyAutoGUI",
                        "status": "active",
                        "requires_key": False,
                        "free": True
                    }
                }
            }
        }
    
    def _save_config(self, config: Optional[Dict] = None):
        """Save configuration to file"""
        if config is None:
            config = self.active_config
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            nervous_system.system(f"Configuration saved to {self.config_file}")
        except Exception as e:
            nervous_system.error("SYSTEM", f"Error saving config: {e}")
    
    def get_active_stack(self) -> Dict:
        """Get currently active technology stack"""
        stack_name = self.active_config.get("active_stack", "default")
        return self.active_config["stacks"].get(stack_name, self.active_config["stacks"]["default"])
    
    def get_active_engine(self, category: str) -> str:
        """Get active engine for a category (stt, tts, llm, motor)"""
        stack = self.get_active_stack()
        return stack.get(category, "")
    
    def switch_engine(self, category: str, engine_name: str) -> bool:
        """
        Hot-swap engine for a category
        Returns True if successful
        """
        # Validate category and engine exist
        if category not in ["stt", "tts", "llm", "motor"]:
            return False
        
        if engine_name not in self.active_config["technologies"].get(category, {}):
            return False
        
        # Update active stack
        stack_name = self.active_config["active_stack"]
        self.active_config["stacks"][stack_name][category] = engine_name
        
        # Save
        self._save_config()
        
        nervous_system.system(f"Switched {category} to {engine_name}")
        return True
    
    def test_engine(self, category: str, engine_name: str) -> Tuple[str, str]:
        """
        Test if an engine is working
        Returns: (status, message)
        status: 'success', 'warning', 'error'
        """
        # This will be implemented to actually test each engine
        # For now, return stored status
        tech_info = self.active_config["technologies"].get(category, {}).get(engine_name, {})
        status = tech_info.get("status", "unknown")
        error_msg = tech_info.get("error_msg", "")
        
        if status == "active":
            return ("success", "Engine is operational")
        elif status == "error":
            return ("error", error_msg)
        else:
            return ("warning", "Engine status unknown")
    
    def create_stack(self, stack_name: str, stt: str, tts: str, llm: str, motor: str) -> bool:
        """Create a new custom stack"""
        self.active_config["stacks"][stack_name] = {
            "stt": stt,
            "tts": tts,
            "llm": llm,
            "motor": motor
        }
        self._save_config()
        nervous_system.system(f"Created stack: {stack_name}")
        return True
    
    def load_stack(self, stack_name: str) -> bool:
        """Load a different stack"""
        if stack_name not in self.active_config["stacks"]:
            return False
        
        self.active_config["active_stack"] = stack_name
        self._save_config()
        nervous_system.system(f"Loaded stack: {stack_name}")
        return True
    
    def get_all_stacks(self) -> Dict:
        """Get all available stacks"""
        return self.active_config["stacks"]
    
    def get_technologies(self, category: str) -> Dict:
        """Get all available technologies for a category"""
        return self.active_config["technologies"].get(category, {})


# Global instance
tech_manager = TechnologyManager()
