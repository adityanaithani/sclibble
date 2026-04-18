# iPod Scrobbler (SCLIbble) - Project Architecture and Context

## Project Goal
A lightweight, terminal-based application to scrobble music from a connected iPod device to Last.fm. The primary focus is on being fast, unobtrusive, and not requiring a full persistent GUI application just to sync a device.

## User Experience (UX) Design: The "Hybrid" Approach
The application uses a **CLI that launches an ephemeral inline TUI** for complex interactive parts.

1.  **Setup/Management (Pure CLI):**
    Commands like `login`, `logout`, and `status` are simple CLI executions that run, print output, and exit.
2.  **The Daily Sync (Inline TUI):**
    When running the `sync` command, the app prints status updates (e.g., finding the iPod, parsing the database). When it's time to select tracks to scrobble, it presents a scrollable checkbox list **inline** within the terminal using a small viewport (e.g., 10 lines). Once the user selects the tracks and hits Enter, the interactive list disappears, leaving a clean summary in the terminal history.
3.  **Graceful Cleanup:**
    Option to delete the `Play Counts` file on the device after successful submission to avoid duplicate scrobbles on future syncs. Option to eject the iPod automatically.

## Technology Stack & Implementation Decisions
*   **CLI Framework:** `Typer` (Lightweight, declarative, built on `click`).
*   **Inline TUI / Prompts:** `Questionary` or `InquirerPy` (Perfect for paginated, inline checkbox lists).
*   **Styling & Output:** `Rich` (For colors, spinners, and formatted terminal text).
*   **Last.fm API:** **Custom Implementation (No `pylast`)**. To minimize dependencies, bloat, and to retain total control, we manually generate the MD5 `api_sig` and make HTTP requests using the `requests` library (or the standard `urllib`). 
    *   *Authentication:* We are utilizing an "Acceptable Risk" approach (hardcoded Shared Secret) or "Bring Your Own Key" (BYOK) for desktop auth, avoiding the need for an external proxy server. This is an intentional trade-off for a small-target-audience CLI tool.
    *   *Batching:* Scrobbles are submitted in chunks of up to 50 tracks via `track.scrobble` using form-encoded indexed payloads (e.g., `artist[0]`).
*   **iPod Parsing:** **Custom Binary Parsing**. We use Python's built-in `struct` module to natively read, parse, and merge the binary `iTunesDB` and `Play Counts` files, completely avoiding heavy external C-based dependencies like `libgpod` or `gpodder` internals.
*   **Caching:** Failed network requests or unsubmitted tracks are saved locally (e.g., `failed_scrobbles.json`) to persist across client restarts.

## Proposed File Structure

```text
sclibble/
├── pyproject.toml         # Dependencies (typer, rich, questionary, requests) & metadata
├── README.md
├── GEMINI.md              # This context file
├── sclibble/              # Main package directory
│   ├── __init__.py
│   ├── main.py            # Typer command definitions and CLI orchestrator
│   ├── ui.py              # Rich and Questionary display logic (the Inline TUI)
│   ├── read.py            # Finding the iPod, and struct-based parsing of iTunesDB/Play Counts
│   ├── last.py            # Custom Last.fm API logic (auth, sig generation, batch scrobbling)
│   ├── config.py          # State management (tokens, failed scrobble cache, settings)
│   └── models.py          # Simple data structures (e.g., Track dataclass)
└── tests/                 # Optional but recommended!
```

## Functionality Breakdown by File

### 1. `models.py` (Data Structures)
Keep things typed and easy to pass around. Use Python `dataclass`es.
*   **`Track`**: A class holding `title`, `artist`, `album`, `play_count`, `last_played`, and computed repeat timestamps.

### 2. `config.py` (State Management)
Handles saving and loading the user's Last.fm session token and local settings.
*   Uses `json` and `pathlib` (or `platformdirs`).
*   **Functions:** `load_session()`, `save_session(session_key)`, `clear_session()`, and managing the `failed_scrobbles` cache.

### 3. `last.py` (The API Wrapper)
Isolates all the Last.fm HTTP logic and signature generation.
*   **`generate_sig(params, secret)`**: Computes the required MD5 signature.
*   **`authenticate_user()`**: Orchestrates fetching a token, opening the browser, waiting for user approval via terminal `input()`, and exchanging the token for a session key.
*   **`scrobble_batch(tracks, session_key)`**: Formats up to 50 tracks into an indexed payload and POSTs them to the API.
*   **`submit_all_scrobbles()`**: Chunks the full tracklist and handles API errors/caching.

### 4. `read.py` (The Device Logic)
Heavy lifting for the hardware side, written natively using Python's `struct` module.
*   **`find_device_path()`**: Scans for the iPod mount point dynamically (e.g., `/Volumes/`).
*   **`read_itunesDb()`**: Unpacks `mhit` and `mhod` headers to extract track metadata.
*   **`read_play_counts()`**: Extracts play counts and timestamps, matching them positionally to the database. Converts Mac epoch timestamps to Unix epoch.
*   **`get_recent_tracks()`**: Merges the data and filters/sorts the un-scrobbled plays. Computes simulated timestamps for repeated plays.

### 5. `ui.py` (The Inline TUI)
Isolates `Rich` and `Questionary` so business logic is separate from terminal drawing.
*   **`show_spinner(text)`**: Uses `Rich` to show a loading animation.
*   **`prompt_track_selection(tracks: list[Track]) -> list[Track]`**: Uses `Questionary.checkbox()` to present the list of tracks, handles pagination, and returns selected tracks.
*   **`print_success()`, `print_error()`, `print_info()`**: Formatted terminal output using `Rich`.

### 6. `cli.py` & `__main__.py` (The Controller)
Wires everything together using `Typer`. Defines the main execution flow: checking auth, finding the iPod, calling `read.py`, prompting the user via `ui.py`, submitting via `last.py`, and handling cleanup (ejecting/deleting Play Counts).
y`, and handling cleanup (ejecting/deleting Play Counts).
