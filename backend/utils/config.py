"""NexuX V9.6 — Configuration"""
import os, platform
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    PROJECT_NAME: str = "NexuX"
    PROJECT_VERSION: str = "9.6.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: str = "*"
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    OUTPUT_DIR: Path = BASE_DIR / "output"
    ASSETS_DIR: Path = BASE_DIR / "assets"

_settings: Optional[Settings] = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

def detect_hardware() -> dict:
    import psutil
    cpu_count = os.cpu_count() or 4
    total_ram_gb = psutil.virtual_memory().total / (1024**3)
    gpu_available = False
    gpu_name = "None"
    try:
        import torch
        if torch.cuda.is_available():
            gpu_available = True
            gpu_name = torch.cuda.get_device_name(0)
    except ImportError:
        pass
    return {
        "cpu_count": cpu_count,
        "total_ram_gb": round(total_ram_gb, 1),
        "gpu_available": gpu_available,
        "gpu_name": gpu_name,
        "os": platform.system(),
    }
