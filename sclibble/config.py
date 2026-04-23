import json
from pathlib import Path
from typing import List, Dict, Optional
from platformdirs import user_data_dir

APP_NAME = "sclibble"

def get_data_dir() -> Path:
    """Returns the platform-specific data directory for the application."""
    data_dir = Path(user_data_dir(APP_NAME))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def get_session_file() -> Path:
    return get_data_dir() / "session.json"

def get_failed_scrobbles_file() -> Path:
    return get_data_dir() / "failed_scrobbles.json"

def save_session(key: str) -> None:
    """Saves the Last.fm session key."""
    session_file = get_session_file()
    session_file.write_text(json.dumps({"session_key": key}))

def load_session() -> Optional[str]:
    """Loads the Last.fm session key."""
    session_file = get_session_file()
    if session_file.exists():
        try:
            data = json.loads(session_file.read_text())
            return data.get("session_key")
        except json.JSONDecodeError:
            return None
    return None

def clear_session() -> None:
    """Clears the stored Last.fm session key."""
    session_file = get_session_file()
    if session_file.exists():
        session_file.unlink()

def save_failed_scrobbles(tracks: List[Dict]) -> None:
    """Saves failed scrobbles to cache."""
    failed_file = get_failed_scrobbles_file()
    failed_file.write_text(json.dumps(tracks))

def load_failed_scrobbles() -> List[Dict]:
    """Loads failed scrobbles from cache."""
    failed_file = get_failed_scrobbles_file()
    if failed_file.exists():
        try:
            return json.loads(failed_file.read_text())
        except json.JSONDecodeError:
            return []
    return []
