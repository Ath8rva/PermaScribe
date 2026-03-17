import yaml
from pathlib import Path

DEFAULT_CONFIG = {
    "recording": {
        "chunk_duration": 30,
        "sample_rate": 16000,
        "silence_threshold": 50,
        "delete_audio_after_transcription": True,
    },
    "transcription": {
        "model": "base",
        "device": "cpu",
        "language": "en",
    },
    "summarization": {
        "model": "deepseek-v3.1:671b-cloud",
        "trigger_time": "18:00",
        "ollama_url": "http://localhost:11434",
        "hourly_chunk_minutes": 60,
    },
    "email": {
        "enabled": False,
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_user": "",
        "smtp_password": "",
        "to": "",
        "subject_prefix": "[PermaScribe]",
    },
    "web": {
        "host": "0.0.0.0",
        "port": 5000,
    },
    "storage": {
        "data_dir": "data",
        "retain_audio_days": 0,
        "retain_transcripts_days": 365,
        "retain_summaries_days": 0,
    },
}

PROJECT_ROOT = Path(__file__).parent.parent


def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config() -> dict:
    config_path = PROJECT_ROOT / "config.yaml"
    if config_path.exists():
        with open(config_path) as f:
            user_config = yaml.safe_load(f) or {}
        return _deep_merge(DEFAULT_CONFIG, user_config)
    return DEFAULT_CONFIG.copy()


def get_data_dir(config: dict) -> Path:
    data_dir = Path(config["storage"]["data_dir"])
    if not data_dir.is_absolute():
        data_dir = PROJECT_ROOT / data_dir
    return data_dir
