# sCLIbble Plan

## v0.1.0 — shipped

Hardening and release prep, all done:

- HTTPS for all Last.fm API calls; timeouts and retry/backoff on requests.
- `submit_scrobbles` no longer mutates the caller's track list.
- Play Counts deletion safety: only deleted when every selected new play was accepted; cache-only retries never delete it.
- Failed-scrobble cache retried automatically on the next sync, with or without a device.
- `status` shows the logged-in username and pending cache count.
- Basic parser validation: file existence/size checks, wrapped parser errors.
- Packaging: `sclibble/__init__.py`, generated artifacts removed from source control, LICENSE, pyproject urls/classifiers.
- Styled UI helpers (success/error/info, spinner, prompts).
- README.

## Roadmap (v0.2+)

### Tests & CI

- Pytest suite for `read.py`, `last.py`, `config.py`, `cli.py` with mocked Last.fm responses and iTunesDB/Play Counts fixtures.
- GitHub Actions CI.

### Windows & Linux

- Validate device discovery (drive letters; `/media`, `/mnt`, `/run/media/<user>`) and timestamp conversion.
- End-to-end run on real hardware per platform.

### Features

- Auto-eject after successful sync/cleanup (`autoeject` toggle).
- Unified `settings` command for viewing/changing prefs.
- Clear-cache command for `failed_scrobbles.json`.
