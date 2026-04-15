# SCLIbble: Notepad

A CLI app built to scrobble play counts from iPods to Last.fm.
(can it also live scrobble from apple music? two birds with one stone!)

## Design

### Requirements:

1. should be an inline CLI/TUI application that allows scrobbling (ie. submitting song played data) to Last.fm from iPod devices.
2. should be able to seamlessly read Play Counts data from the iPod, with track data (artist, album, song) and play data (last played, number of repeats)
3. should be able to compute estimated replay times by last played time, song length, and number of replays
4. should be able to assemble payloads with the song/playing data to submit to the user's last.fm account through the last.fm API.

### Detailed Requirements

1. find iPod (disk mode necessary) mounted at /Volumes/iPod
2. find / confirm Play Counts file exists at iTunesDB/Play Counts
3. read iTunesDB / Play Counts:
   1. read iTunesDB
   2. read Play Counts file to retrieve play count/last played/skip count/last skipped data
   3. merge/match Play Counts with iTunesDB
4. build payloads for last.fm API
   1. filter down to songs where play time is longer than 30 seconds + track played for min(4 mins, 50% time duration)
   2. compute repeats
      1. last played time - (number of repeats \* song length time)
   3. artist, album, song title
   4. package into single payload
   5. send through last.fm API to previously authenticated user account
5. gracefully handle cleanup
   1. option to delete Play Counts file (manually chosen or configured in settings)
   2. option to eject ipod/drive (manually chosen or config in settings)

### Flow

1. user invokes TUI or CLI
2. check for lastfm authentication
   1. if previously authenticated, move on to 3
   2. if not, send user to lastfm browser authentication
3. look for connected, mounted, accessible iPod
   1. if already exists user specified path, use that
   2. otherwise, default to Volumes/iPod or Volumes/IPOD (does case matter for folders in a filesystem?)
4. find iTunesDB folder, iTunesDB file, Play Counts file
5. read database files, generate/assemble database file
6. read assembled database file, compute play counts
7. assemble computed play counts into lastfm-api-compatible format, combine all into payload (how does api work? submit as one big payload or multiple individual requests?)
8. present to user, option to delete or upload
9. upload to lastfm
10. graceful exit procedures (delete, eject options)

### Settings

- lastfm account authorization / logout
- y/n automatically delete play counts after submission
- y/n automatically eject ipod after submission
- change saved drive path / erase

## Dev Checklist:

- [] authenticate with Last.fm
- [] find mounted iPod as drive, find iTunesDB / Play Counts
- [x] read/parse/merge iTunesDB / Play Counts
- [] build payloads for Last.fm API
  - compute repeat times
  - filter to Last.fm definition of "listened to"
  - only 50 songs per batch request, if needed split into multiple
  - store unsubmitted songs in a cache that survives client restarts until sent
- [] send to Last.fm
- [] cleanup
- [] terminal UI
- [] config/settings file, persistent settings

## FileMap:

```
sclibble/
		- test /
		- scripts/
				- last.py - handles authenticating with, building payloads for, sending requests to lastfm API
				- read.py - handles reading/parsing itunesdb/play count files from ipod
		- main.py - runs the main functionality

```
