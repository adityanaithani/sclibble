# sclibble

_scrobble + CLI = sCLIbble_

Fast, lightweight CLI that scrobbles plays from an iPod to Last.fm.

I found popular tools like Legacy Scrobbler 1) too slow to parse large databases, and 2) unnecessary to launch a whole Electron GUI just to sync and close.

## Install

```
pip install sclibble
```

```
pipx install sclibble
```

Requires Python 3.9.

## Quickstart

1. `sclibble login` — authenticates via browser to Last.fm
2. Connect your iPod _in disk mode_ (required)
3. `sclibble sync` — finds the device, parses new plays, and asks you to review / confirm before submitting
4. Done. Any rejects are cached and retried automatically on the following sync

## Commands

> [!NOTE] these may also be run with the `scl` alias

- `sclibble login` — authenticates via browser to Last.fm
- `sclibble logout` — logs out of current Last.fm session
- `sclibble sync` — find connected iPod, parse new plays, review/select, scrobble; also retries cached failures
- `sclibble status` — show logged-in username and pending cached scrobbles
- `sclibble delete` — toggle auto-deletion of `Play Counts` after a fully successful sync. (you want this OFF if you're syncing with both iTunes and Last.fm!)
- `sclibble path` — set or unset a custom iPod mount path

## Configuration

### Folder locations:

- macOS: `~/Library/Application Support/sclibble/`
- Windows: `C:\Users\<username>\AppData\Local\adityanaithani\sclibble`
- Linux: `~/.local/share/sclibble`

### Parameters

- `config.json` — preferences: `autodelete` toggle and `custom_path` setting
- `session.json` — Last.fm session key, cached username
- `failed_scrobbles.json` — cache of failed scrobbles

## How it works

- iPods store two binary database files in the `iPod_Control` directory:
  1. `iTunesDB` - contains track metadata for every song on the device
  2. `Play Counts` - list of last-played tracks, play counts (of course), last-played timestamp
- sclibble scans common mount points (or a custom path) for the directory, parses the database files, then matches `Play_Counts` positionally against `iTunesDB`. Timestamps are also converted from mac -> unix epoch and adjusted to match local timezone
- For each track, `Play Counts` stores one last-played timestamp + a play count. For repeat plays, sclibble simulates one timestamp per listen by backdating from the last-played time by the track length, then resolves overlaps so plays are chronological
- Scrobbles are submitted to the Last.fm API in batches of <=50. Transient failures are handled by timeouts and retry/backoff
- Failed scrobbles are cached in `failed_scrobbles.json` and automatically retried on next `sclibble sync`
- The `Play Counts` file is _offered_ for deletion when every selected new play was accepted by Last.fm and the failure cache is empty. Cache-only retries never delete it, so play data is never wiped before it's safely scrobbled

## Compatibility

Currently only tested and confirmed working on macOS with an iPod Mini 2G. Windows/Linux code does exist but I don't have a machine to test it on.

If you are able to test on a different OS or with a different device please create an issue and let me know so I can update this section.

## Credentials

I will note that sclibble ships with hardcoded keys, which is _mega_ insecure, but unfortunately the Last.fm API is quite old and doesn't have security features like modern APIs. For the super limited scope I imagine this tool will have I'm okay with it for now, if usage picks up I may switch to a proxy via a secure web server.

## Dev Roadmap

- [ ] Tests and CI
- [ ] Windows / Linux validation
- [ ] Auto-eject post sync
- [ ] Improve settings UX
- [ ] Clear cache command

## License

MIT — see `LICENSE`.
