import os


class Config:
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
    OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
    RATE_LIMIT = os.environ.get("RATE_LIMIT", "5 per minute")
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    GAME_SETTINGS = {
        "initial_health": 100,
        "max_inventory": 5,
        "difficulty_modifiers": {"easy": 0.8, "medium": 1.0, "hard": 1.2},
    }
