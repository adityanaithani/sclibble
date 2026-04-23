from typing import List, Optional
from contextlib import contextmanager

from rich.console import Console
from rich.spinner import Spinner
from rich.live import Live
from rich.text import Text
import questionary

from sclibble.models import Track

console = Console()

def print_success(message: str) -> None:
    """Prints a success message in green."""
    console.print(f"[bold green]✓[/bold green] {message}")

def print_error(message: str) -> None:
    """Prints an error message in red."""
    console.print(f"[bold red]✗[/bold red] {message}")

def print_info(message: str) -> None:
    """Prints an info message in blue."""
    console.print(f"[bold blue]i[/bold blue] {message}")

@contextmanager
def show_spinner(text: str):
    """Context manager to show a spinner during a long-running task."""
    with Live(Spinner("dots", text=Text(text, style="cyan")), refresh_per_second=10, transient=True) as live:
        yield

def prompt_track_selection(tracks: List[Track]) -> List[Track]:
    """
    Presents a checkbox list for the user to select which tracks to scrobble.
    Returns the list of selected Track instances.
    """
    if not tracks:
        return []

    # Create choices for questionary
    choices = []
    for i, track in enumerate(tracks):
        # Format a nice label: "Title - Artist"
        label = f"{track.title} - {track.artist}"
        if track.album:
            label += f" ({track.album})"
            
        choices.append(
            questionary.Choice(
                title=label,
                value=i,
                checked=True  # default to checked
            )
        )

    selected_indices = questionary.checkbox(
        "Select tracks to scrobble:",
        choices=choices,
        instruction="(Space to toggle, Enter to confirm)",
        qmark="?",
        pointer=">",
    ).ask()

    # If user cancels (e.g. Ctrl+C), selected_indices will be None
    if selected_indices is None:
        return []

    return [tracks[i] for i in selected_indices]

def prompt_confirm(message: str, default: bool = False) -> bool:
    """Prompts the user for a yes/no confirmation."""
    return questionary.confirm(message, default=default).ask()
