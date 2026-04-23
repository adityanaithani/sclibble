import pytest
import responses
from unittest.mock import patch

from sclibble.models import Track
from sclibble.last import (
    generate_sig,
    fetch_request_token,
    fetch_session_key,
    scrobble_batch,
    submit_scrobbles,
    url as last_url
)

def test_generate_sig():
    params = {"method": "auth.getToken", "api_key": "test_key", "format": "json"}
    secret = "test_secret"
    # Expected: sort by key -> api_keytest_keymethodauth.getTokentest_secret
    # MD5 of above
    sig = generate_sig(params, secret)
    assert isinstance(sig, str)
    assert len(sig) == 32

@responses.activate
def test_fetch_request_token():
    responses.add(
        responses.GET,
        last_url,
        json={"token": "test_token_123"},
        status=200
    )
    
    token = fetch_request_token("key", "secret")
    assert token == "test_token_123"

@responses.activate
def test_scrobble_batch():
    responses.add(
        responses.POST,
        last_url,
        json={"scrobbles": {"@attr": {"accepted": 1, "ignored": 0}}},
        status=200
    )
    
    tracks = [
        Track(title="Song", artist="Artist", album="Album", play_count=1, last_played=0, timestamp=123)
    ]
    
    response = scrobble_batch(tracks, "key", "secret", "session_key")
    assert response["scrobbles"]["@attr"]["accepted"] == 1

@patch("sclibble.last.scrobble_batch")
@patch("sclibble.last.load_failed_scrobbles")
@patch("sclibble.last.save_failed_scrobbles")
def test_submit_scrobbles(mock_save, mock_load, mock_scrobble_batch):
    # Mock cache to return nothing
    mock_load.return_value = []
    
    # Mock scrobble to succeed
    mock_scrobble_batch.return_value = {"scrobbles": {"@attr": {"accepted": 2}}}
    
    tracks = [
        Track(title="S1", artist="A1", album="", play_count=1, last_played=0, timestamp=100),
        Track(title="S2", artist="A2", album="", play_count=1, last_played=0, timestamp=200)
    ]
    
    successful = submit_scrobbles(tracks, "test_session_key")
    
    assert successful == 2
    mock_save.assert_called_once_with([]) # cleared cache
