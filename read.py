import struct
import time
import os


def read_itunesDb(filepath):
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


def read_play_counts(filepath, tracklist):
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


def get_recent_tracks(itunesDb_path, play_counts_path):
    tracklist = read_itunesDb(itunesDb_path)
    tracklist = read_play_counts(play_counts_path, tracklist)

    recent_plays = [t for t in tracklist if t["playCount"] > 0]
    recent_plays.sort(key=lambda x: x["lastPlayed"], reverse=True)

    return recent_plays


# --- Usage Example ---
if __name__ == "__main__":
    itunesDb_file = "./test/sampleData/iTunesDB"
    play_counts_file = "./test/sampleData/Play Counts"

    total = read_itunesDb(itunesDb_file)
    print(f"Found {len(total)} tracks, processing...")

    recent = get_recent_tracks(itunesDb_file, play_counts_file)
    print(f"Found {len(recent)} recent plays ready to scrobble. \n")
    print(f"tracks:\n {recent}")
    pass
