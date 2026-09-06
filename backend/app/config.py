from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/voxshield"
    AASIST_CHECKPOINT_PATH: str = "weights/AASIST.pth"
    AASIST_CONFIG_PATH: str = "aasist/config/AASIST.conf"
    WHISPER_MODEL_SIZE: str = "base"
    RISK_THRESHOLD_PASS: float = 0.3
    RISK_THRESHOLD_CHALLENGE: float = 0.6
    UPLOAD_DIR: str = "uploads"
    WEIGHT_CLONE: float = 0.40
    WEIGHT_SOCIAL_ENG: float = 0.25
    WEIGHT_SPEAKER: float = 0.20
    WEIGHT_TRUST: float = 0.10
    WEIGHT_TRANSACTION: float = 0.05

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
