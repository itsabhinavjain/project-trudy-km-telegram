"""Sync command - Combined fetch + process workflow.

This is a convenience command that runs both phases in sequence.
"""

import asyncio
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console

from src.cli.fetch import _fetch_async
from src.cli.process import _process_async
from src.core.logger import setup_logging

console = Console()


def sync_cmd(
    ctx: typer.Context,
    users: Optional[List[str]] = typer.Argument(
        None,
        help="Specific users to sync (usernames). Leave empty for all users.",
    ),
    all: bool = typer.Option(
        True,
        "--all",
        help="Sync all users",
    ),
    user: Optional[List[str]] = typer.Option(
        None,
        "--user",
        "-u",
        help="Sync specific user (can be used multiple times)",
    ),
    full: bool = typer.Option(
        False,
        "--full",
        help="Full sync - fetch all historical messages",
    ),
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        help="Limit number of messages to fetch per user",
    ),
    skip_transcription: bool = typer.Option(
        False,
        "--skip-transcription",
        help="Skip audio/video transcription",
    ),
    skip_ocr: bool = typer.Option(
        False,
        "--skip-ocr",
        help="Skip OCR text extraction",
    ),
    skip_summarization: bool = typer.Option(
        False,
        "--skip-summarization",
        help="Skip AI summarization",
    ),
    skip_tags: bool = typer.Option(
        False,
        "--skip-tags",
        help="Skip automatic tag generation",
    ),
    workers: int = typer.Option(
        3,
        "--workers",
        "-w",
        help="Number of parallel processing workers",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview what would be synced without writing files",
    ),
):
    """Sync messages from Telegram - combined fetch + process workflow.

    This is a convenience command that runs both phases in sequence:
    1. Fetch: Downloads messages from Telegram to staging
    2. Process: Processes staging files into enriched markdown

    This is the most common command for day-to-day usage.

    Examples:
        # Incremental sync for all users (default)
        trudy sync

        # Full sync of all historical messages
        trudy sync --full

        # Sync specific user
        trudy sync --user alice

        # Quick sync without AI features
        trudy sync --skip-transcription --skip-ocr --skip-summarization

        # Preview what would be synced
        trudy sync --dry-run
    """
    # Get context
    config_path = ctx.obj.get("config_path", Path("config/config.yaml"))
    verbose = ctx.obj.get("verbose", False)
    quiet = ctx.obj.get("quiet", False)

    # Setup logging
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level=log_level)

    # Determine which users to sync
    users_to_sync = None
    if user:  # --user option takes precedence
        users_to_sync = user
    elif users:  # Positional arguments
        users_to_sync = users
    elif not all:
        console.print("[yellow]No users specified. Use --all to sync all users.[/yellow]")
        raise typer.Exit(1)

    # Build skip options for processing
    skip_options = {
        "transcription": skip_transcription,
        "ocr": skip_ocr,
        "summarization": skip_summarization,
        "tags": skip_tags,
        "links": False,  # Always extract links
    }

    try:
        if not quiet:
            console.print("[bold cyan]Trudy 2.0 - Full Sync[/bold cyan]")
            console.print("[dim]Running fetch + process in sequence[/dim]")
            console.print()

        # Run sync operation
        asyncio.run(
            _sync_async(
                config_path=config_path,
                users=users_to_sync,
                full_sync=full,
                limit=limit,
                skip_options=skip_options,
                workers=workers,
                dry_run=dry_run,
                quiet=quiet,
            )
        )

    except KeyboardInterrupt:
        console.print("\n[yellow]Sync cancelled by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


async def _sync_async(
    config_path: Path,
    users: Optional[List[str]],
    full_sync: bool,
    limit: Optional[int],
    skip_options: dict,
    workers: int,
    dry_run: bool,
    quiet: bool,
):
    """Async sync implementation."""
    # Phase 1: Fetch
    if not quiet:
        console.print("[bold]Phase 1: Fetch[/bold]")
        console.print()

    try:
        await _fetch_async(
            config_path=config_path,
            users=users,
            full_sync=full_sync,
            limit=limit,
            dry_run=dry_run,
            quiet=quiet,
        )
    except Exception as e:
        console.print(f"[red]Fetch phase failed: {e}[/red]")
        raise

    if not quiet:
        console.print()
        console.print("[bold]Phase 2: Process[/bold]")
        console.print()

    # Phase 2: Process
    try:
        await _process_async(
            config_path=config_path,
            users=users,
            date=None,  # Process all dates
            skip_options=skip_options,
            reprocess=False,  # Only process new/changed files
            workers=workers,
            dry_run=dry_run,
            quiet=quiet,
        )
    except Exception as e:
        console.print(f"[red]Process phase failed: {e}[/red]")
        raise

    if not quiet:
        console.print()
        console.print("[bold green]✓ Sync complete![/bold green]")
