import json
import os
from datetime import datetime

LOG_FILE = "output/error_log.json"


def log_error(context, error_type, message, url=None):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "context": context,
        "error_type": error_type,
        "message": str(message),
        "url": url or "N/A",
    }

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                log = json.load(f)
        except (json.JSONDecodeError, OSError):
            log = []
    else:
        log = []

    log.append(entry)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

    print(f"[ERROR] {context}/{error_type}: {message}")


def load_errors():
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def clear_errors():
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)