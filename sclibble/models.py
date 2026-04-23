from dataclasses import dataclass
from typing import Optional

@dataclass
class Track:
    title: str
    artist: str
    album: str
    play_count: int
    last_played: int
    timestamp: Optional[int] = None
