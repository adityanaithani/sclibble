from typing import List, Optional
from contextlib import contextmanager
from rich.console import Console
from rich.spinner import Spinner
from rich.live import Live
from rich.text import Text
from rich.theme import Theme
import questionary
from questionary import Style
from sclibble.models import Track

# declare custom themes
questionary_theme = Style(
    [
        ("qmark", "ansibrightcyan bold"),  # token in front of the question
        ("question", "ansibrightcyan bold"),  # question text
        ("answer", "ansiyellow"),  # submitted answer text behind the question
        (
            "pointer",
            "ansiblue bold",
        ),  # pointer used in select and checkbox prompts
        (
            "highlighted",
            "fg:ansigreen bold",
        ),  # pointed-at choice in select and checkbox prompts
        (
            "selected",
            "noreverse",
        ),  # style for a selected item of a checkbox
        ("separator", ""),  # separator in lists
        (
            "instruction",
            "ansibrightblack italic",
        ),  # user instructions for select, rawselect, checkbox
        ("text", ""),  # plain text
        (
            "disabled",
            "",
        ),  # disabled choices for select and checkbox prompts
    ]
)


rich_theme = Theme(
    {
        "repr.number": "bold green",  # numbers
        "repr.path": "bold blue",  # file paths
        "repr.bool_true": "bold cyan",  # 'true' variable
        "repr.bool_false": "bold red",  # 'false' variable
    }
)

console = Console(theme=rich_theme)


def print_success(message: str) -> None:
    """Prints a success message in green."""
    # console.print(f"[bold green]•[/bold green] {message}")
    console.print(f"{message}")


def print_error(message: str) -> None:
    """Prints an error message in red."""
    # console.print(f"[bold red]✗[/bold red] {message}")
    console.print(f"{message}")


def print_info(message: str) -> None:
    """Prints an info message in blue."""
    # console.print(f"[bold blue]•[/bold blue] {message}")
    console.print(f"{message}")


@contextmanager
def show_spinner(text: str):
    """Context manager to show a spinner during a long-running task."""
    with Live(
        Spinner("dots2", text=Text(text, style="green")),
        refresh_per_second=10,
        transient=True,
    ) as live:
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
        # Format label
        label = f"{track.title} - {track.artist}"
        if track.album:
            label += f" - {track.album}"

        choices.append(
            questionary.Choice(title=label, value=i, checked=True)  # default to checked
        )

    selected_indices = questionary.checkbox(
        "Select tracks to scrobble:",
        choices=choices,
        instruction="(Space: toggle, Enter: confirm, A: select/deselect all)",
        qmark="?",
        pointer=">",
        style=questionary_theme,
    ).ask()

    # keyboard interrupt / cancel condition
    if selected_indices is None:
        return []

    return [tracks[i] for i in selected_indices]


def prompt_confirm(message: str, default: bool = False) -> bool:
    """Prompts the user for a yes/no confirmation."""
    return questionary.confirm(
        message,
        default=default,
        style=questionary_theme,
        auto_enter=False,
    ).ask()
