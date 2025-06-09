import os
from typing import List, Dict, Any


class Config:
    """Configuration management for Labubu Monitor"""

    # Database settings
    DB_PATH = os.getenv("DB_PATH", "labubu_monitor.db")

    # Monitoring settings
    CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "30"))  # seconds
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))  # seconds

    # URLs to monitor
    DEFAULT_URLS = [
        "https://www.popmart.com/us/products/1898/THE-MONSTERS-Let's-Checkmate-Series-Vinyl-Plush-Doll"
    ]

    # OpenAI settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

    # Notification settings
    ENABLE_EMAIL = os.getenv("ENABLE_EMAIL", "false").lower() == "true"
    EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
    EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))
    EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_TO = os.getenv("EMAIL_TO", "").split(",") if os.getenv("EMAIL_TO") else []

    ENABLE_WEBHOOK = os.getenv("ENABLE_WEBHOOK", "false").lower() == "true"
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

    ENABLE_DISCORD = os.getenv("ENABLE_DISCORD", "false").lower() == "true"
    DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

    ENABLE_SLACK = os.getenv("ENABLE_SLACK", "false").lower() == "true"
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

    # Web dashboard settings
    WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
    WEB_PORT = int(os.getenv("WEB_PORT", "8080"))
    SECRET_KEY = os.getenv("SECRET_KEY", "labubu-monitor-secret-key")

    # Logging settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "labubu_monitor.log")

    @classmethod
    def get_urls(cls) -> List[str]:
        """Get URLs from environment or default"""
        urls_env = os.getenv("MONITOR_URLS", "")
        if urls_env:
            return [url.strip() for url in urls_env.split(",") if url.strip()]
        return cls.DEFAULT_URLS

    @classmethod
    def validate(cls) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []

        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required")

        if cls.ENABLE_EMAIL:
            if not cls.EMAIL_USERNAME or not cls.EMAIL_PASSWORD:
                errors.append("Email credentials required when ENABLE_EMAIL=true")
            if not cls.EMAIL_TO:
                errors.append("EMAIL_TO required when ENABLE_EMAIL=true")

        if cls.ENABLE_WEBHOOK and not cls.WEBHOOK_URL:
            errors.append("WEBHOOK_URL required when ENABLE_WEBHOOK=true")

        if cls.ENABLE_DISCORD and not cls.DISCORD_WEBHOOK_URL:
            errors.append("DISCORD_WEBHOOK_URL required when ENABLE_DISCORD=true")

        if cls.ENABLE_SLACK and not cls.SLACK_WEBHOOK_URL:
            errors.append("SLACK_WEBHOOK_URL required when ENABLE_SLACK=true")

        return errors
