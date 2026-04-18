# SCLIbble Implementation Plan

Based on the investigation of the existing codebase and the `GEMINI.md` architecture document, here is the plan to complete the application. 

Currently, `pyproject.toml`, `config.py`, `models.py`, `cli.py`, and `__main__.py` are empty files. `last.py` and `read.py` contain functional (but partially incomplete) logic. `ui.py` is missing. 

## Phase 1: Project Setup & Tooling
*   **`pyproject.toml`**: Configure build system using standard `setuptools` to ensure standard installability via `pip` or `brew`. Declare metadata and dependencies (`typer`, `rich`, `questionary`, `requests`, `platformdirs`). Define a CLI entry point for `sclibble`.
*   **`__main__.py`**: Setup standard python `-m sclibble` execution to invoke the Typer app.

## Phase 2: Core Data Models & State (`models.py`, `config.py`)
*   **`models.py`**: Implement a `Track` `dataclass` to replace raw dictionaries. Include attributes: `title` (maps to `"track"` in `read.py`), `artist`, `album`, `play_count`, `last_played`, and a calculated `timestamp` for Last.fm submission.
*   **`config.py`**: Implement persistent state using `platformdirs` to determine standard OS-specific data directories.
    *   Functions: `load_session()`, `save_session(key)`, `clear_session()`.
    *   Functions: `load_failed_scrobbles()`, `save_failed_scrobbles(tracks)`.

## Phase 3: Hardware & Parsing Completion (`read.py`)
*   Refactor the output of `read_itunesDb` and `read_play_counts` to yield instances of the `Track` dataclass.
*   **Implement Cross-Platform `find_device_path()`**: Scan for the iPod mount point (e.g., under `/Volumes/` on macOS, typical mount points on Linux, or removable drives on Windows).
*   **Implement Repeated Plays Logic**: Currently, `get_recent_tracks` just checks `playCount > 0`. We need to simulate timestamps for tracks played multiple times since the last sync. 
    *   Logic: For a given track, subtract the track length in seconds from the `lastPlayed` timestamp to simulate the previous play. 
    *   Conflict Resolution: Implement logic to ensure these simulated backdated timestamps do not overlap with the timestamps of *other* tracks played in between.

## Phase 4: Last.fm API Refinement (`last.py`)
*   Refactor to accept lists of `Track` dataclass instances rather than raw dictionaries.
*   Enhance error handling to correctly trap failed batches and interface with `config.py`'s cache.
*   Retain the hardcoded API Key / Secret as defined in `GEMINI.md`'s acceptable risk approach.

## Phase 5: Inline TUI (`ui.py`)
*   Create `ui.py` to handle all user-facing interactions.
*   Implement `Rich` logic: `show_spinner(text)` and formatted feedback (`print_success`, `print_info`, `print_error`).
*   Implement `Questionary` logic: `prompt_track_selection(tracks)` to render a scrollable inline checkbox list (e.g., limited to 10-15 lines) returning the subset of selected `Track` instances.

## Phase 6: CLI Orchestrator (`cli.py`)
*   Implement the `Typer` app and register commands:
    *   `login`: Triggers the browser auth flow and saves the session key.
    *   `logout`: Clears the stored session key.
    *   `status`: Prints current auth status and pending scrobble cache.
    *   `sync`: 
        1. Finds iPod.
        2. Parses database & play counts.
        3. Prompts via TUI.
        4. Submits scrobbles.
        5. Prompts for cleanup (delete Play Counts, eject device).
