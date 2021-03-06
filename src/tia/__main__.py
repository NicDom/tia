"""__main__ of tia."""
from typing import Optional

from enum import Enum

import typer
from rich.console import Console

from tia import version  # type: ignore[attr-defined]

# from random import choice


class Color(str, Enum):
    """Colors for the CI."""

    white = "white"
    red = "red"
    cyan = "cyan"
    magenta = "magenta"
    yellow = "yellow"
    green = "green"


app = typer.Typer(
    name="tia",
    help="A Tax and Invoice Assistant (TIA)",
    add_completion=False,
)
console = Console()


def version_callback(print_version: Optional[bool]) -> None:  # pragma: no cover
    """Print the version of the package."""
    if print_version:
        console.print(f"[yellow]tia[/] version: [bold blue]{version}[/]")
        raise typer.Exit()


@app.command(name="")
def main(
    name: str = typer.Option(..., help="Person to greet."),
    color: Optional[Color] = typer.Option(
        None,
        "-c",
        "--color",
        "--colour",
        case_sensitive=False,
        help="Color for print. If not specified then choice will be random.",
    ),
    print_version: Optional[bool] = typer.Option(
        None,
        "-v",
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Prints the version of the tia package.",
    ),
) -> None:
    """Print a greeting with a giving name."""
    # if color is None:
    #     color = choice(list(Color))

    # greeting: str = hello(name)
    console.print(f"[bold {color}]TIA[/]")


if __name__ == "__main__":
    app()  # pragma: no cover
