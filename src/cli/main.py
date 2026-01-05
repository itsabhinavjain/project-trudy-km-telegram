"""Trudy 2.0 CLI - Main entry point using Typer.

This module defines the main Typer application and registers all subcommands.
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

# Initialize Typer app
app = typer.Typer(
    name="trudy",
    help="Trudy 2.0 - Personal Knowledge Management Bot for Telegram",
    add_completion=False,
)

# Initialize Rich console for pretty output
console = Console()

# Version
__version__ = "2.0.0"


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    config: Optional[Path] = typer.Option(
        Path("config/config.yaml"),
        "--config",
        "-c",
        help="Path to configuration file",
        exists=False,  # Don't validate existence here, let commands handle it
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging (DEBUG level)",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress non-error output",
    ),
    version: bool = typer.Option(
        False,
        "--version",
        help="Show version and exit",
    ),
):
    """Trudy 2.0 - Personal Knowledge Management Bot.

    A two-phase Telegram bot that:
    1. Fetches messages to staging area (fetch phase)
    2. Processes and enriches to final markdown (process phase)

    Features:
    - Auto-discovery of users
    - Incremental sync with state tracking
    - Media download and organization
    - AI features: transcription, summarization, OCR, tagging
    - Link metadata extraction
    - Rich YAML metadata in processed markdown
    """
    # Handle version flag
    if version:
        console.print(f"Trudy version {__version__}")
        raise typer.Exit()

    # Store context for commands to access
    if ctx.obj is None:
        ctx.obj = {}

    ctx.obj["config_path"] = config
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet


# Import and register subcommands
from src.cli.discover import discover_cmd
from src.cli.fetch import fetch_cmd
from src.cli.process import process_cmd
from src.cli.status import info_cmd, status_cmd
from src.cli.sync import sync_cmd
from src.cli.utils import clean_cmd

# Register commands
app.command(name="discover")(discover_cmd)
app.command(name="fetch")(fetch_cmd)
app.command(name="process")(process_cmd)
app.command(name="sync")(sync_cmd)
app.command(name="status")(status_cmd)
app.command(name="info")(info_cmd)
app.command(name="clean")(clean_cmd)


def main():
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    main()
