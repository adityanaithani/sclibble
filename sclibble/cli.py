import os
from pathlib import Path
import typer

from sclibble.config import load_session, save_session, clear_session, load_failed_scrobbles
from sclibble.last import authenticate, submit_scrobbles
from sclibble.read import find_device_path, get_recent_tracks
from sclibble.ui import (
    print_success,
    print_error,
    print_info,
    show_spinner,
    prompt_track_selection,
    prompt_confirm,
)

app = typer.Typer(help="SCLIbble: The lightweight iPod scrobbler for Last.fm.")

@app.command()
def login():
    """Authenticate with Last.fm and save the session key."""
    if load_session():
        print_info("You are already logged in.")
        if not prompt_confirm("Do you want to re-authenticate?"):
            return

    try:
        print_info("Opening browser to authenticate with Last.fm...")
        session_key = authenticate()
        save_session(session_key)
        print_success("Successfully authenticated and saved session key.")
    except Exception as e:
        print_error(f"Failed to authenticate: {e}")


@app.command()
def logout():
    """Clear the stored Last.fm session key."""
    clear_session()
    print_success("Logged out successfully.")


@app.command()
def status():
    """Check current authentication status and pending scrobbles."""
    session_key = load_session()
    if session_key:
        print_success("You are logged in.")
    else:
        print_error("You are not logged in. Run `sclibble login` first.")

    failed_cache = load_failed_scrobbles()
    if failed_cache:
        print_info(f"There are {len(failed_cache)} pending/failed scrobbles in the cache.")
    else:
        print_info("There are no pending scrobbles in the cache.")


@app.command()
def sync():
    """Find iPod, parse tracks, select what to scrobble, and submit."""
    session_key = load_session()
    if not session_key:
        print_error("You must be logged in to sync. Run `sclibble login` first.")
        raise typer.Exit(1)

    # 1. Find Device
    with show_spinner("Searching for iPod..."):
        device_path = find_device_path()
        
    if not device_path:
        print_error("Could not find a connected iPod (iPod_Control directory missing).")
        raise typer.Exit(1)
        
    print_success(f"Found iPod at {device_path}")

    itunesDb_file = Path(device_path) / "iPod_Control" / "iTunes" / "iTunesDB"
    play_counts_file = Path(device_path) / "iPod_Control" / "iTunes" / "Play Counts"

    if not itunesDb_file.exists() or not play_counts_file.exists():
        print_error("Required database files (iTunesDB or Play Counts) not found on device.")
        raise typer.Exit(1)

    # 2. Parse Database
    with show_spinner("Parsing iTunesDB and Play Counts..."):
        recent_tracks = get_recent_tracks(str(itunesDb_file), str(play_counts_file))

    # Append cached failures to list for selection (optional, but good for visibility)
    cached_failures = load_failed_scrobbles()
    if not recent_tracks and not cached_failures:
        print_info("No recent plays found to scrobble.")
        return

    print_info(f"Found {len(recent_tracks)} un-scrobbled plays on device.")
    if cached_failures:
        print_info(f"Also found {len(cached_failures)} cached failed scrobbles.")

    # 3. Prompt Selection
    selected_tracks = prompt_track_selection(recent_tracks)
    if not selected_tracks and not cached_failures:
        print_info("No tracks selected. Sync cancelled.")
        return

    # 4. Submit Scrobbles
    with show_spinner("Submitting scrobbles to Last.fm..."):
        # The submit_scrobbles function automatically loads and appends the cache internally
        successful_count = submit_scrobbles(selected_tracks, session_key)
        
    print_success(f"Successfully scrobbled {successful_count} tracks.")

    # 5. Cleanup
    if successful_count > 0:
        if prompt_confirm("Do you want to delete the Play Counts file to prevent duplicate scrobbles next time?"):
            try:
                os.remove(play_counts_file)
                print_success("Play Counts file deleted.")
            except Exception as e:
                print_error(f"Failed to delete Play Counts file: {e}")

    # Not strictly required, but a nice to have from GEMINI.md
    if prompt_confirm("Do you want to eject the iPod?"):
        print_info("Please eject the iPod manually using your OS (OS-specific auto-eject not yet fully implemented).")

if __name__ == "__main__":
    app()
