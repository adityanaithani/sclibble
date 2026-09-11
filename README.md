# sCLIbble

sclibble scrobbles plays from a physical iPod to Last.fm. With the iPod connected in disk mode, it parses the on-device `iTunesDB` and `Play Counts` files directly, shows you the new plays it found, and submits them after you confirm. Anything Last.fm doesn't accept is cached locally and retried automatically on the next sync.

## Install

Recommended (installs into an isolated environment):

```
pipx install sclibble
```

Plain pip works too:

```
pip install sclibble
```

Requires Python 3.9+. macOS is the tested platform. Both `sclibble` and the shorter `scl` alias are installed.

## Quickstart

1. `sclibble login` — opens your browser for the Last.fm authorization flow.
2. Connect your iPod in disk mode.
3. `sclibble sync` — finds the device, parses new plays, and asks you to review and confirm the selection before submitting.
4. Done. Anything Last.fm rejects is cached and retried automatically next time.

## Commands

- `sclibble login` — authenticate with Last.fm via the browser flow and save the session.
- `sclibble logout` — delete the saved session.
- `sclibble sync` — find the iPod, parse new plays, review/select them, and scrobble; also retries cached failures, and can retry cache-only when no iPod is connected.
- `sclibble status` — show the logged-in username and the number of pending cached scrobbles.
- `sclibble delete` — toggle auto-deletion of `Play Counts` after a fully successful sync.
- `sclibble path` — set or unset a custom iPod mount path.

Data lives in the platformdirs user-data directory — on macOS, `~/Library/Application Support/sclibble/`:

- `config.json` — preferences: the `autodelete` toggle and `custom_path` setting.
- `session.json` — Last.fm session key and cached username.
- `failed_scrobbles.json` — cache of scrobbles that failed, retried on the next sync.

## How it works

- Device discovery scans common mount points (or your custom path set via `sclibble path`) for an `iPod_Control` directory.
- Two binary files are parsed on-device: `iTunesDB` (track metadata — title, artist, album, length) and `Play Counts` (play count and last-played timestamp per track, matched positionally against the iTunesDB track order). Timestamps are converted from Mac epoch to Unix epoch and adjusted for the local timezone.
- iPods store one last-played timestamp plus a play count per track. For repeat plays, sclibble simulates one timestamp per listen by backdating from the last-played time by the track length, then resolves overlaps so plays are chronological.
- Scrobbles are submitted to the Last.fm API over HTTPS in batches of up to 50, with timeouts and retry/backoff on transient failures.
- Failed scrobbles land in the local cache (`failed_scrobbles.json`) and are retried automatically on the next sync — even without a device connected.
- The `Play Counts` file is only offered for deletion when every selected new play was accepted by Last.fm and the failure cache is empty. Cache-only retries never delete it, so play data is never wiped before it's safely scrobbled.

## Platform notes

macOS is tested. Windows and Linux discovery code exists (drive letters on Windows; `/media`, `/mnt`, `/run/media/<user>` on Linux) but is untested.

## Troubleshooting

- **iPod not found** — make sure disk mode is enabled and the device contains the `iPod_Control` folder. If your OS mounts the iPod somewhere unusual, set that path with `sclibble path`.
- **Scrobbles failing** — failures are cached locally and retried automatically on the next `sclibble sync`, even without an iPod connected. Check `sclibble status` for the pending count.
- **Old plays rejected** — Last.fm rejects scrobbles older than 14 days. Sync regularly so older plays don't get dropped.

## API key note

sclibble ships with hardcoded Last.fm app credentials, which is standard practice for installed Last.fm desktop clients. If you'd rather use your own API key, request one at <https://www.last.fm/api/accounts>.

## Roadmap

- Tests and CI.
- Windows and Linux validation.
- Auto-eject after sync.
- Settings UX improvements.
- Clear-cache command.

## License

MIT — see `LICENSE`.
