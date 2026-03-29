from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """應用設定，從環境變數或 .env 載入"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Gemini API
    gemini_api_key: str = ""

    # PostgreSQL（支援 Zeabur 注入的 POSTGRES_URI 格式）
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/videometa"
    postgres_uri: str = ""  # Zeabur 自動注入，格式為 postgresql://...

    @property
    def resolved_database_url(self) -> str:
        """優先使用 POSTGRES_URI（Zeabur），自動轉換為 asyncpg 格式"""
        url = self.postgres_uri or self.database_url
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # 應用設定
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    storage_path: Path = Path("./storage")
    max_concurrent_analysis: int = 5

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    @property
    def videos_path(self) -> Path:
        path = self.storage_path / "videos"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def thumbnails_path(self) -> Path:
        path = self.storage_path / "thumbnails"
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
