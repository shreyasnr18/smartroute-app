import json
import os
from pathlib import Path
from typing import Any, Dict

CONFIG_FILE = Path(__file__).parent.parent / "config.json"

DEFAULT_CONFIG = {
    "CAPACITY_THRESHOLD": 10,
    "TIME_BUCKET_MINUTES": 15,
    "USE_MOCK_TRAFFIC": True,
    "USE_MOCK_LLM": True,
    "GOOGLE_MAPS_API_KEY": "",
    "GEMINI_API_KEY": "",
    "FIREBASE_CREDENTIALS_PATH": "",
    "FIREBASE_PROJECT_ID": "smartroute-demo-live",
    "RAZORPAY_KEY_ID": "rzp_test_mockkeyid12345",
    "RAZORPAY_KEY_SECRET": "rzp_test_mocksecret12345",
    "PARKING_SPOT_EXPIRY_MINUTES": 15,
    "ENFORCE_COMPLIANCE_GUARDRAILS": True,
    "DB_PATH": "smartroute.db",
    "HOST": "127.0.0.1",
    "PORT": 8000
}

def load_config() -> Dict[str, Any]:
    """Loads configuration from config.json with environment variable overrides."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    else:
        data = {}

    config = DEFAULT_CONFIG.copy()
    config.update(data)

    # Allow environment variables to override values
    if os.getenv("CAPACITY_THRESHOLD"):
        config["CAPACITY_THRESHOLD"] = int(os.getenv("CAPACITY_THRESHOLD"))
    if os.getenv("USE_MOCK_TRAFFIC"):
        config["USE_MOCK_TRAFFIC"] = os.getenv("USE_MOCK_TRAFFIC").lower() in ("true", "1", "yes")
    if os.getenv("USE_MOCK_LLM"):
        config["USE_MOCK_LLM"] = os.getenv("USE_MOCK_LLM").lower() in ("true", "1", "yes")
    if os.getenv("GOOGLE_MAPS_API_KEY"):
        config["GOOGLE_MAPS_API_KEY"] = os.getenv("GOOGLE_MAPS_API_KEY")
    if os.getenv("GEMINI_API_KEY"):
        config["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")
    if os.getenv("FIREBASE_CREDENTIALS_PATH"):
        config["FIREBASE_CREDENTIALS_PATH"] = os.getenv("FIREBASE_CREDENTIALS_PATH")
    if os.getenv("FIREBASE_PROJECT_ID"):
        config["FIREBASE_PROJECT_ID"] = os.getenv("FIREBASE_PROJECT_ID")
    if os.getenv("RAZORPAY_KEY_ID"):
        config["RAZORPAY_KEY_ID"] = os.getenv("RAZORPAY_KEY_ID")
    if os.getenv("RAZORPAY_KEY_SECRET"):
        config["RAZORPAY_KEY_SECRET"] = os.getenv("RAZORPAY_KEY_SECRET")
    if os.getenv("PARKING_SPOT_EXPIRY_MINUTES"):
        config["PARKING_SPOT_EXPIRY_MINUTES"] = int(os.getenv("PARKING_SPOT_EXPIRY_MINUTES"))

    return config

def save_config(new_config: Dict[str, Any]) -> None:
    """Updates and saves config.json."""
    current = load_config()
    current.update(new_config)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)

def get_capacity_threshold() -> int:
    return int(load_config().get("CAPACITY_THRESHOLD", 10))

def get_time_bucket_minutes() -> int:
    return int(load_config().get("TIME_BUCKET_MINUTES", 15))

def use_mock_traffic() -> bool:
    cfg = load_config()
    return cfg.get("USE_MOCK_TRAFFIC", True) or not bool(cfg.get("GOOGLE_MAPS_API_KEY", "").strip())

def use_mock_llm() -> bool:
    cfg = load_config()
    return cfg.get("USE_MOCK_LLM", True) or not bool(cfg.get("GEMINI_API_KEY", "").strip())

def get_parking_expiry_minutes() -> int:
    return int(load_config().get("PARKING_SPOT_EXPIRY_MINUTES", 15))
