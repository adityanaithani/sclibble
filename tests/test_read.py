import os
from pathlib import Path
from sclibble.read import read_itunesDb, read_play_counts, get_recent_tracks

SAMPLE_DATA_DIR = Path(__file__).parent / "sampleData"
ITUNES_DB_PATH = SAMPLE_DATA_DIR / "iTunesDB"
PLAY_COUNTS_PATH = SAMPLE_DATA_DIR / "Play Counts"

def test_read_itunesDb():
    if not ITUNES_DB_PATH.exists():
        return # Skip if sample data is not present
        
    tracklist = read_itunesDb(str(ITUNES_DB_PATH))
    assert len(tracklist) > 0
    assert "track" in tracklist[0]
    assert "artist" in tracklist[0]
    assert "album" in tracklist[0]
    assert "playCount" in tracklist[0]
    assert "lastPlayed" in tracklist[0]

def test_get_recent_tracks():
    if not ITUNES_DB_PATH.exists() or not PLAY_COUNTS_PATH.exists():
        return
        
    recent_tracks = get_recent_tracks(str(ITUNES_DB_PATH), str(PLAY_COUNTS_PATH))
    
    # We should have some tracks extracted from the sample data
    assert len(recent_tracks) > 0
    
    # Verify the overlap logic sorted them correctly by timestamp ascending
    for i in range(len(recent_tracks) - 1):
        assert recent_tracks[i].timestamp <= recent_tracks[i+1].timestamp
        
    # Verify they are correctly mapped to Track dataclasses
    assert hasattr(recent_tracks[0], "title")
    assert hasattr(recent_tracks[0], "artist")
    assert recent_tracks[0].play_count == 1  # Logic expands multiple plays to single ones
