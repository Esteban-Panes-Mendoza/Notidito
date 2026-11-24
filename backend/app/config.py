import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Notidito API"
    DATABASE_URL: str = "postgresql://notidito_user:notidito_pass@localhost:5432/notidito_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET_KEY: str = "super_secreto_notidito_jwt"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    AUDIVERIS_PATH: str = "audiveris"
    STORAGE_DIR: str = "./storage"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def audio_uploads_dir(self) -> str:
        path = os.path.join(self.STORAGE_DIR, "uploads", "audio")
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def score_uploads_dir(self) -> str:
        path = os.path.join(self.STORAGE_DIR, "uploads", "scores")
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def midi_outputs_dir(self) -> str:
        path = os.path.join(self.STORAGE_DIR, "outputs", "midi")
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def musicxml_outputs_dir(self) -> str:
        path = os.path.join(self.STORAGE_DIR, "outputs", "musicxml")
        os.makedirs(path, exist_ok=True)
        return path

settings = Settings()