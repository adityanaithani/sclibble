import os
from pathlib import Path
import typer
import typer.rich_utils

from sclibble.config import (
    load_session,
    save_session,
    clear_session,
    load_username,
    save_username,
    load_failed_scrobbles,
    load_prefs,
    save_prefs,
)
from sclibble.last import authenticate, fetch_username, submit_scrobbles
from sclibble.read import find_device_path, get_recent_tracks, get_device_name
from sclibble.ui import (
    print_success,
    print_error,
    print_info,
    show_spinner,
    prompt_track_selection,
    prompt_confirm,
)

app = typer.Typer(
    no_args_is_help=True, rich_markup_mode="rich", help="CLI iPod Scrobbler."
)


@app.command()
def sync():
    """Scrobble to Last.fm."""
    session_key = load_session()
    if not session_key:
        print_error("You must be logged in to sync. Run `sclibble login` first.")
        raise typer.Exit(1)

    prefs = load_prefs()
    custom_path = prefs.get("custom_path")
    autodelete = prefs.get("autodelete")

    # find device
    with show_spinner("Searching for iPod..."):
        device_path = find_device_path(custom_path)

    if not device_path:
        cached_failures = load_failed_scrobbles()
        if cached_failures and prompt_confirm(
            f"No iPod found — retry {len(cached_failures)} cached scrobbles?"
        ):
            with show_spinner("Scrobbling..."):
                successful_count = submit_scrobbles([], session_key)
            print_success(f"Successfully scrobbled {successful_count} tracks.")
        else:
            print_error("Could not find a connected iPod.")
            raise typer.Exit(1)
        return

    device_name = get_device_name(device_path)
    if device_name:
        print_success(f"Found {device_name}")
    else:
        print_success(f"Found iPod at {device_path}")

    itunesDb_file = Path(device_path) / "iPod_Control" / "iTunes" / "iTunesDB"
    play_counts_file = Path(device_path) / "iPod_Control" / "iTunes" / "Play Counts"

    if not itunesDb_file.exists() or not play_counts_file.exists():
        print_error(
            "Required database files not found on device. Go listen to some music!"
        )
        raise typer.Exit(1)

    # parse / join database
    with show_spinner("Parsing database..."):
        recent_tracks = get_recent_tracks(str(itunesDb_file), str(play_counts_file))

    # cached failures appended to list for visibility
    cached_failures = load_failed_scrobbles()
    if not recent_tracks and not cached_failures:
        print_info("No recent plays found to scrobble.")
        return

    print_info(f"Found {len(recent_tracks)} new plays.")
    if cached_failures:
        print_info(f"Also found {len(cached_failures)} cached failed scrobbles.")

    # track selection prompt
    selected_tracks = prompt_track_selection(recent_tracks)
    if not selected_tracks and not cached_failures:
        print_info("No tracks selected. Sync cancelled.")
        return

    with show_spinner("Scrobbling..."):
        successful_count = submit_scrobbles(selected_tracks, session_key)

    print_success(f"Successfully scrobbled {successful_count} tracks.")

    # only delete Play Counts if every selected new device play was
    # accepted by Last.fm and nothing landed (back) in the failure cache.
    remaining_failures = load_failed_scrobbles()
    all_accepted = (
        bool(selected_tracks)
        and successful_count >= len(selected_tracks) + len(cached_failures)
        and not remaining_failures
    )

    if successful_count > 0 and all_accepted:
        should_delete = (
            autodelete
            if autodelete is not None
            else prompt_confirm("Delete Play Counts?")
        )
        if should_delete:
            try:
                os.remove(play_counts_file)
                print_success("Play Counts deleted.")
            except Exception as e:
                print_error(f"Failed to delete Play Counts: {e}")
    elif not all_accepted:
        print_info(
            "Play Counts kept on device: some scrobbles failed or were not "
            "accepted. Failed tracks are cached for the next sync."
        )


@app.command()
def status():
    """Current authentication status and pending scrobbles."""
    session_key = load_session()
    if session_key:
        username = load_username()
        if username:
            print_success(f"Logged in as {username}.")
        else:
            print_success("Logged in to Last.fm.")
    else:
        print_error("You are not logged in. Run `sclibble login` first.")

    failed_cache = load_failed_scrobbles()
    if failed_cache:
        print_info(
            f"There are {len(failed_cache)} pending/failed scrobbles in the cache."
        )
    else:
        print_info("There are no pending scrobbles in the cache.")


@app.command(rich_help_panel="Authentication")
def login():
    """Login to Last.fm."""
    if load_session():
        print_info("You are already logged in.")
        if not prompt_confirm("Re-authenticate?"):
            return

    try:
        print_info("Opening browser to authenticate with Last.fm...")
        session_key = authenticate()
        save_session(session_key)
        print_success("Successfully authenticated and saved session key.")
        try:
            username = fetch_username(session_key)
            save_username(username)
            print_info(f"Logged in as {username}.")
        except Exception as e:
            print_info(f"Could not fetch username: {e}")
    except Exception as e:
        print_error(f"Failed to authenticate: {e}")


@app.command(rich_help_panel="Authentication")
def logout():
    """Logout of Last.fm."""
    clear_session()
    print_success("Logged out successfully.")


@app.command(rich_help_panel="Settings")
def delete():
    """Toggle auto-delete Play Counts after scrobbling."""
    prefs = load_prefs()
    current_setting = prefs.get("autodelete", False)
    new_setting = not current_setting
    prefs["autodelete"] = new_setting
    save_prefs(prefs)
    status = "enabled" if new_setting else "disabled"
    print_success(f"{status} Play Counts deletion after scrobbling.")


@app.command(rich_help_panel="Settings")
def path():
    """Change default iPod mount path."""
    prefs = load_prefs()
    current_path = prefs.get("custom_path", "")
    print_info(f"Current custom path: {current_path or 'Not set'}")
    new_path = typer.prompt(
        "Enter new custom path (leave blank to unset)",
        default="",
        show_default=False,
    )
    if new_path:
        prefs["custom_path"] = new_path
        save_prefs(prefs)
        print_success(f"Custom path set to: {new_path}")
    else:
        if "custom_path" in prefs:
            del prefs["custom_path"]
            save_prefs(prefs)
            print_success("Custom path unset.")
        else:
            print_info("No custom path was set.")


if __name__ == "__main__":
    app()
