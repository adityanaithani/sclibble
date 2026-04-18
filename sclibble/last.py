import hashlib
import requests
import webbrowser

# /* SECRETSECRETSECRET */
api_key = "2b8fa2046f72f0a442d28d9671ab4fbb"
secret = "ed3c377b301baebf3cfdea19d153c8ef"
# /* SECRETSECRETSECRET */

url = "http://ws.audioscrobbler.com/2.0/"


# HELPERS
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

    r = requests.get(url, params=payload)
    r.raise_for_status()

    return r.json()["lfm"]["token"]


def fetch_session_key(key: str, secret: str, token: str) -> str:
    payload = {
        "method": "auth.getSession",
        "token": token,
        "api_key": key,
        "format": "json",
    }
    payload["api_sig"] = generate_sig(payload, secret)

    r = requests.get(url, params=payload)
    r.raise_for_status()

    return r.json()["lfm"]["session"]["key"]


# ORCHESTRATOR
def authenticate():
    # 1. get token
    token = fetch_request_token(api_key, secret)
    # 2. open browser for user
    auth_url = f"http://www.last.fm/api/auth/?api_key={api_key}&token={token}"
    webbrowser.open(auth_url)
    # 3. wait for user to finish
    # 4. exchange token for session key
    session_key = fetch_session_key(api_key, secret, token)
    # 5. save session key
    return session_key


def scrobble_batch(tracklist_chunk: list, api_key: str, secret: str, session_key: str):
    if len(tracklist_chunk) > 50:
        raise ValueError("Cannot scrobble more than 50 tracks per batch!")

    payload = {
        "method": "track.scrobble",
        "api_key": api_key,
        "sk": session_key,
        "format": "json",
    }

    for i, track in enumerate(tracklist_chunk):
        # artist, track, timestamp, album-opt, chosenbyuser-opt, tracknumber-opt, albumartist-opt, duration-opt)
        payload[f"artist[{i}]"] = track["artist"]
        payload[f"track[{i}]"] = track["track"]
        payload[f"timestamp[{i}]"] = track["timestamp"]  # needs to be computed
        if track.get("album"):
            payload[f"album[{i}]"] = track["album"]
        payload["api_sig"] == generate_sig(payload, secret)

        response = requests.post(url, data=payload)
        response.raise_for_status()

        return response.json()


def submit_scrobbles(tracklist: list, api_key: str, secret: str, session_key: str):
    chunk_size = 50
    total_scrobbles = 0

    # print submitting batch of tracks
    for i in range(0, len(tracklist), chunk_size):
        chunk = tracklist[i : i + chunk_size]

        try:
            result = scrobble_batch(chunk, api_key, secret, session_key)
            accepted = result.get("scrobbles", {}).get("@attr", {}).get("accepted", 0)
            total_scrobbles += int(accepted)

        except Exception as e:
            # save to cache
            # print failed to scrobble
            pass
