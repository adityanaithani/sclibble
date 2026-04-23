from sclibble.models import Track

def test_track_creation():
    track = Track(
        title="Test Song",
        artist="Test Artist",
        album="Test Album",
        play_count=1,
        last_played=1234567890,
        timestamp=1234567890
    )
    assert track.title == "Test Song"
    assert track.artist == "Test Artist"
    assert track.album == "Test Album"
    assert track.play_count == 1
    assert track.last_played == 1234567890
    assert track.timestamp == 1234567890

def test_track_defaults():
    track = Track(
        title="Test Song",
        artist="Test Artist",
        album="",
        play_count=0,
        last_played=0
    )
    assert track.timestamp is None
