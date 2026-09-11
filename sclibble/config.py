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


def get_prefs_file() -> Path:
    return get_data_dir() / "config.json"


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


def save_username(username: str) -> None:
    """Saves the Last.fm username alongside the session key."""
    session_file = get_session_file()
    data = {}
    if session_file.exists():
        try:
            data = json.loads(session_file.read_text())
        except json.JSONDecodeError:
            data = {}
    data["username"] = username
    session_file.write_text(json.dumps(data))


def load_username() -> Optional[str]:
    """Loads the stored Last.fm username, if present."""
    session_file = get_session_file()
    if session_file.exists():
        try:
            data = json.loads(session_file.read_text())
            return data.get("username")
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


def save_prefs(prefs: Dict) -> None:
    """Saves user preferences to config.json."""
    prefs_file = get_prefs_file()
    prefs_file.write_text(json.dumps(prefs))


def load_prefs() -> Dict:
    """Loads user preferences from config.json."""

    prefs_file = get_prefs_file()
    if prefs_file.exists():
        try:
            return json.loads(prefs_file.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def clear_prefs() -> None:
    """Clears stored user preferences."""

    prefs_file = get_prefs_file()
    if prefs_file.exists():
        prefs_file.unlink()
