import struct
import time
import sys
from pathlib import Path
from typing import List, Optional

from sclibble.models import Track


def find_device_path() -> Optional[str]:
    """Scans common mount points for an iPod (identified by iPod_Control directory)."""
    if sys.platform == "win32":
        import string
        drives = [f"{d}:\\" for d in string.ascii_uppercase]
        for drive in drives:
            try:
                ipod_path = Path(drive) / "iPod_Control"
                if ipod_path.exists() and ipod_path.is_dir():
                    return drive
            except Exception:
                pass
    elif sys.platform == "darwin":
        volumes_dir = Path("/Volumes")
        if volumes_dir.exists():
            for mount in volumes_dir.iterdir():
                try:
                    ipod_path = mount / "iPod_Control"
                    if ipod_path.exists() and ipod_path.is_dir():
                        return str(mount)
                except Exception:
                    pass
    else:  # Linux and others
        import getpass
        try:
            user = getpass.getuser()
        except Exception:
            user = ""
            
        search_paths = [Path("/media"), Path("/mnt")]
        if user:
            search_paths.append(Path(f"/run/media/{user}"))
            
        for sp in search_paths:
            if sp.exists():
                for mount in sp.iterdir():
                    try:
                        ipod_path = mount / "iPod_Control"
                        if ipod_path.exists() and ipod_path.is_dir():
                            return str(mount)
                    except Exception:
                        pass
    return None


def read_itunesDb(filepath: str) -> List[dict]:
    tracklist = []

    with open(filepath, "rb") as f:
        data = f.read()

    offset = 0
    while True:
        offset = data.find(b"mhit", offset)
        if offset == -1:
            break

        mhit_pos = offset

        header_size = struct.unpack_from("<I", data, mhit_pos + 4)[0]
        mhod_entries_count = struct.unpack_from("<I", data, mhit_pos + 12)[0]
        track_id = struct.unpack_from("<I", data, mhit_pos + 16)[0]
        track_length = struct.unpack_from("<I", data, mhit_pos + 40)[0]

        track = {
            "id": track_id,
            "length": track_length,
            "track": "",
            "album": "",
            "artist": "",
            "playCount": 0,
            "lastPlayed": 0,
        }

        mhod_pos = mhit_pos + header_size
        for _ in range(mhod_entries_count):
            if mhod_pos + 16 > len(data):
                break

            total_size = struct.unpack_from("<I", data, mhod_pos + 8)[0]
            mhod_type = struct.unpack_from("<I", data, mhod_pos + 12)[0]

            if mhod_type in (1, 3, 4):
                string_length = struct.unpack_from("<I", data, mhod_pos + 28)[0]
                string_data = data[mhod_pos + 40 : mhod_pos + 40 + string_length]
                decoded_string = string_data.decode("utf-16-le", errors="ignore")

                if mhod_type == 1:
                    track["track"] = decoded_string
                elif mhod_type == 3:
                    track["album"] = decoded_string
                elif mhod_type == 4:
                    track["artist"] = decoded_string

            mhod_pos += total_size

        tracklist.append(track)
        offset += 4
    return tracklist


def read_play_counts(filepath: str, tracklist: List[dict]) -> List[dict]:
    with open(filepath, "rb") as f:
        data = f.read()

    entry_len = struct.unpack_from("<I", data, 8)[0]
    num_entries = struct.unpack_from("<I", data, 12)[0]

    bytes_offset = 96

    tz_offset_seconds = -time.localtime().tm_gmtoff

    for i in range(num_entries - 1):
        if i >= len(tracklist):
            break

        play_count = struct.unpack_from("<I", data, bytes_offset)[0]

        if play_count > 0:
            last_played = struct.unpack_from("<I", data, bytes_offset + 4)[0]

            # mac epoc to unix epoc
            last_played -= 2082844800
            last_played += tz_offset_seconds

            tracklist[i]["playCount"] = play_count
            tracklist[i]["lastPlayed"] = last_played

        bytes_offset += entry_len

    return tracklist


def get_recent_tracks(itunesDb_path: str, play_counts_path: str) -> List[Track]:
    """
    Parses the database and play counts, returning a list of `Track` models.
    Simulates timestamps for multiple plays of the same track to prevent overlap.
    """
    tracklist = read_itunesDb(itunesDb_path)
    tracklist = read_play_counts(play_counts_path, tracklist)

    class Play:
        def __init__(self, track_dict: dict, ts: int):
            self.track_dict = track_dict
            self.ts = ts

    plays = []
    for t in tracklist:
        pc = t["playCount"]
        if pc > 0:
            length_sec = t["length"] // 1000
            if length_sec <= 0:
                length_sec = 180  # Default to 3 minutes if length is missing or 0
            
            last_played = t["lastPlayed"]
            for i in range(pc):
                # Backdate previous plays by the length of the track
                ts = last_played - (i * length_sec)
                plays.append(Play(t, ts))

    # Sort plays descending by calculated timestamp to resolve overlaps
    plays.sort(key=lambda p: p.ts, reverse=True)

    resolved_tracks = []
    latest_available_time = float('inf')

    for p in plays:
        if p.ts > latest_available_time:
            p.ts = latest_available_time

        length_sec = p.track_dict["length"] // 1000
        if length_sec <= 0:
            length_sec = 180

        # The next (older) play must finish before this one starts
        latest_available_time = p.ts - length_sec
        
        # We model each scrobble event as a Track instance with play_count=1
        track_model = Track(
            title=p.track_dict["track"],
            artist=p.track_dict["artist"],
            album=p.track_dict["album"],
            play_count=1, 
            last_played=p.track_dict["lastPlayed"],
            timestamp=int(p.ts)
        )
        resolved_tracks.append(track_model)

    # Return chronologically ascending
    resolved_tracks.sort(key=lambda t: t.timestamp)
    return resolved_tracks


# --- Usage Example ---
if __name__ == "__main__":
    device_path = find_device_path()
    print(f"Device Path: {device_path}")
    
    itunesDb_file = "../tests/sampleData/iTunesDB"
    play_counts_file = "../tests/sampleData/Play Counts"

    if Path(itunesDb_file).exists() and Path(play_counts_file).exists():
        recent = get_recent_tracks(itunesDb_file, play_counts_file)
        print(f"Found {len(recent)} recent plays ready to scrobble. \n")
        for tr in recent[:5]:
            print(tr)
        if len(recent) > 5:
            print(f"... and {len(recent) - 5} more.")
    else:
        print("Sample data not found.")
