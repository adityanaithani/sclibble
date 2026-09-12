import hashlib
import time
import requests
import webbrowser
from typing import List

from sclibble.models import Track
from sclibble.config import save_failed_scrobbles, load_failed_scrobbles

# intentionally hardcoded credentials (last.fm api is really really old)
api_key = "2b8fa2046f72f0a442d28d9671ab4fbb"
secret = "ed3c377b301baebf3cfdea19d153c8ef"

url = "https://ws.audioscrobbler.com/2.0/"

TIMEOUT = 30
MAX_RETRIES = 3

# helpers


def _request_with_retry(method: str, **kwargs) -> requests.Response:
    """HTTP request with retry: up to 3 attempts, backing off 1s then 2s.
    Only retries on connection errors, timeouts, and 5xx responses."""
    kwargs.setdefault("timeout", TIMEOUT)
    for attempt in range(MAX_RETRIES):
        if attempt:
            time.sleep(attempt)  # 1s before 2nd attempt, 2s before 3rd
        try:
            response = requests.request(method, url, **kwargs)
            if response.status_code < 500:
                return response
        except (requests.ConnectionError, requests.Timeout):
            if attempt == MAX_RETRIES - 1:
                raise
    return response  # final attempt got a 5xx; let the caller handle it


# Last.fm API signature
def generate_sig(params: dict, secret: str) -> str:
    filtered_params = {
        k: v for k, v in params.items() if k not in ("format", "callback", "api_sig")
    }
    sorted_params = sorted(filtered_params.items())
    sig_string = "".join(f"{k}{v}" for k, v in sorted_params)
    sig_string += secret
    return hashlib.md5(sig_string.encode("utf-8")).hexdigest()


def fetch_request_token(key: str, secret: str) -> str:
    payload = {"method": "auth.getToken", "api_key": key, "format": "json"}
    payload["api_sig"] = generate_sig(payload, secret)

    r = _request_with_retry("get", params=payload)
    r.raise_for_status()

    return r.json()["token"]


def fetch_session_key(key: str, secret: str, token: str) -> str:
    payload = {
        "method": "auth.getSession",
        "token": token,
        "api_key": key,
        "format": "json",
    }
    payload["api_sig"] = generate_sig(payload, secret)

    r = _request_with_retry("get", params=payload)
    if r.status_code != 200:
        error_msg = r.text
        try:
            error_msg = r.json().get("message", r.text)
        except Exception:
            pass
        raise Exception(f"Last.fm API Error ({r.status_code}): {error_msg}")

    return r.json()["session"]["key"]


def fetch_username(session_key: str) -> str:
    """Fetches the account username for a session key via user.getInfo."""
    payload = {
        "method": "user.getInfo",
        "api_key": api_key,
        "sk": session_key,
        "format": "json",
    }
    payload["api_sig"] = generate_sig(payload, secret)

    r = _request_with_retry("get", params=payload)
    r.raise_for_status()

    return r.json()["user"]["name"]


# orchestrators
def authenticate() -> str:
    # 1. get token
    token = fetch_request_token(api_key, secret)
    # 2. open browser for user
    auth_url = f"https://www.last.fm/api/auth/?api_key={api_key}&token={token}"
    webbrowser.open(auth_url)
    # 3. wait for user to finish (handled by CLI caller)
    input(
        "Press Enter here after you have authorized the application in your browser..."
    )
    # 4. exchange token for session key
    session_key = fetch_session_key(api_key, secret, token)
    # 5. return session key to be saved by the caller
    return session_key


def scrobble_batch(
    tracklist_chunk: List[Track], api_key: str, secret: str, session_key: str
) -> dict:
    if len(tracklist_chunk) > 50:
        raise ValueError("Cannot scrobble more than 50 tracks per batch!")

    payload = {
        "method": "track.scrobble",
        "api_key": api_key,
        "sk": session_key,
        "format": "json",
    }

    for i, track in enumerate(tracklist_chunk):
        payload[f"artist[{i}]"] = track.artist
        payload[f"track[{i}]"] = track.title
        payload[f"timestamp[{i}]"] = str(track.timestamp)
        if track.album:
            payload[f"album[{i}]"] = track.album

    payload["api_sig"] = generate_sig(payload, secret)

    response = _request_with_retry("post", data=payload)
    if response.status_code != 200:
        error_msg = response.text
        try:
            error_msg = response.json().get("message", response.text)
        except Exception:
            pass
        raise Exception(f"Last.fm API Error ({response.status_code}): {error_msg}")

    return response.json()


def submit_scrobbles(tracklist: List[Track], session_key: str) -> int:
    chunk_size = 50
    total_scrobbles = 0
    failed_tracks = []

    # load any previously failed scrobbles and combine them with the current
    # list (on a copy, so the caller's list is never mutated)
    combined = list(tracklist)
    for item in load_failed_scrobbles():
        combined.append(
            Track(
                title=item["title"],
                artist=item["artist"],
                album=item["album"],
                play_count=item["play_count"],
                last_played=item["last_played"],
                timestamp=item["timestamp"],
            )
        )

    # process combined list in chunks of 50 (last.fm API limit)
    for i in range(0, len(combined), chunk_size):
        chunk = combined[i : i + chunk_size]

        try:
            result = scrobble_batch(chunk, api_key, secret, session_key)
            accepted = result.get("scrobbles", {}).get("@attr", {}).get("accepted", 0)
            total_scrobbles += int(accepted)
        except Exception as e:
            failed_tracks.extend(chunk)

    if failed_tracks:
        # convert Track objects to dicts for saving in cache
        failures_to_save = [
            {
                "title": t.title,
                "artist": t.artist,
                "album": t.album,
                "play_count": t.play_count,
                "last_played": t.last_played,
                "timestamp": t.timestamp,
            }
            for t in failed_tracks
        ]
        save_failed_scrobbles(failures_to_save)
    else:
        # if successful, clear cache
        save_failed_scrobbles([])

    return total_scrobbles
