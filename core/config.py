import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Cargar .env explícitamente desde la raíz del proyecto
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

class Settings(BaseSettings):
    # Core
    AGENT_MODE: str = "CLOUD"
    WAKE_WORD: str = "computadora"
    MIC_DEVICE_INDEX: int | None = None  # Auto-detect by default

    # Brain (SambaNova)
    SAMBANOVA_API_KEY: str | None = None
    SAMBANOVA_URL: str = "https://api.sambanova.ai/v1"

    # Porcupine
    PICOVOICE_ACCESS_KEY: str | None = None

    # Ear (HuggingFace)
    HUGGINGFACE_API_KEY: str | None = None
    HUGGINGFACE_WHISPER_URL: str = "https://api-inference.huggingface.co/models/openai/whisper-large-v3"
    
    # Voice
    ELEVENLABS_API_KEY: str | None = None
    ELEVENLABS_VOICE_ID: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8", 
        extra="ignore"
    )

    @property
    def is_cloud_mode(self):
        return self.AGENT_MODE.upper() == "CLOUD"

    @property
    def has_openai_key(self):
        return self.OPENAI_API_KEY is not None and self.OPENAI_API_KEY.startswith("sk-")

settings = Settings()

if __name__ == "__main__":
    print(f"Modo Cargado: {settings.AGENT_MODE}")
    print(f"¿Tiene llave OpenAI?: {settings.has_openai_key}")
    print(f"¿Tiene llave ElevenLabs?: {settings.ELEVENLABS_API_KEY is not None}")
