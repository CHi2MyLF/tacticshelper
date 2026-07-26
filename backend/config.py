"""应用配置管理"""

import os
import json
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "backend" / "data"
DB_PATH = BASE_DIR / "data" / "fm_advisor.db"
CONFIG_PATH = BASE_DIR / "data" / "config.json"


class AppConfig(BaseModel):
    """应用配置"""
    api_key: str = ""
    api_base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"  # deepseek-chat / deepseek-v4-pro / claude-sonnet-4-20250514
    language: str = "zh"


def load_config() -> AppConfig:
    """加载配置"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return AppConfig(**data)
    return AppConfig()


def save_config(config: AppConfig) -> None:
    """保存配置"""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config.model_dump(), f, indent=2, ensure_ascii=False)
