import json
from unittest.mock import patch
from pathlib import Path

from sclibble.config import (
    save_session,
    load_session,
    clear_session,
    save_failed_scrobbles,
    load_failed_scrobbles,
)

@patch("sclibble.config.get_data_dir")
def test_session_management(mock_get_data_dir, tmp_path):
    mock_get_data_dir.return_value = tmp_path

    # Initially none
    assert load_session() is None

    # Save session
    save_session("test_key_123")
    assert load_session() == "test_key_123"

    # Clear session
    clear_session()
    assert load_session() is None

@patch("sclibble.config.get_data_dir")
def test_failed_scrobbles_management(mock_get_data_dir, tmp_path):
    mock_get_data_dir.return_value = tmp_path

    # Initially empty
    assert load_failed_scrobbles() == []

    # Save failures
    failures = [{"title": "Song", "artist": "Artist", "album": "Album", "play_count": 1, "last_played": 0, "timestamp": 0}]
    save_failed_scrobbles(failures)
    
    loaded = load_failed_scrobbles()
    assert len(loaded) == 1
    assert loaded[0]["title"] == "Song"
