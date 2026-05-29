import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # LLM
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral:7b")
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    # OCR
    OCR_CONFIDENCE_HIGH = 0.75
    OCR_CONFIDENCE_MEDIUM = 0.45
    TESSERACT_CONFIG = "--psm 6 --oem 3"

    # App
    APP_TITLE = "Medicine Explainer"
    APP_SUBTITLE = "Simple explanations for your medicines"
    MAX_IMAGE_SIZE_MB = 10
    SUPPORTED_FORMATS = ["jpg", "jpeg", "png", "bmp", "tiff"]

    # Database
    DB_PATH = os.getenv("DB_PATH", "data/medicine_cache.db")

    # Safety
    ALWAYS_SHOW_DISCLAIMER = True
    MIN_MEDICINE_NAME_LENGTH = 4
