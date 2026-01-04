"""Fetch command - Downloads messages from Telegram to staging area.

This implements Phase 1 of the two-phase workflow: Fetch → Staging
"""

import asyncio
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from src.core.config import load_config
from src.core.logger import get_logger, setup_logging
from src.core.state import StateManager
from src.markdown.staging_writer import StagingWriter
from src.telegram.client import TelegramClient
from src.telegram.downloader import MediaDownloader
from src.telegram.fetcher import MessageFetcher

console = Console()
logger = get_logger(__name__)


def fetch_cmd(
    ctx: typer.Context,
    users: Optional[List[str]] = typer.Argument(
        None,
        help="Specific users to fetch (usernames). Leave empty for all users.",
    ),
    all: bool = typer.Option(
        True,
        "--all",
        help="Fetch for all discovered users",
    ),
    user: Optional[List[str]] = typer.Option(
        None,
        "--user",
        "-u",
        help="Fetch for specific user (can be used multiple times)",
    ),
    full: bool = typer.Option(
        False,
        "--full",
        help="Full sync - fetch all historical messages (ignores last_message_id)",
    ),
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        help="Limit number of messages to fetch per user",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview what would be fetched without writing files",
    ),
):
    """Fetch messages from Telegram and write to staging area.

    This command implements Phase 1 of the two-phase workflow:
    - Connects to Telegram Bot API
    - Discovers users (auto-discovery mode)
    - Fetches new messages (incremental sync by default)
    - Downloads media to shared media folder
    - Writes messages to staging markdown files
    - Updates fetch_state in state.json

    Examples:
        # Fetch new messages for all users (incremental sync)
        trudy fetch

        # Fetch all historical messages (full sync)
        trudy fetch --full

        # Fetch for specific user
        trudy fetch --user alice

        # Fetch for multiple users
        trudy fetch --user alice --user bob

        # Preview without writing files
        trudy fetch --dry-run
    """
    # Get context
    config_path = ctx.obj.get("config_path", Path("config/config.yaml"))
    verbose = ctx.obj.get("verbose", False)
    quiet = ctx.obj.get("quiet", False)

    # Setup logging
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level=log_level)

    # Determine which users to fetch
    users_to_fetch = None
    if user:  # --user option takes precedence
        users_to_fetch = user
    elif users:  # Positional arguments
        users_to_fetch = users
    elif not all:
        console.print("[yellow]No users specified. Use --all to fetch for all users.[/yellow]")
        raise typer.Exit(1)

    try:
        # Run async fetch operation
        asyncio.run(
            _fetch_async(
                config_path=config_path,
                users=users_to_fetch,
                full_sync=full,
                limit=limit,
                dry_run=dry_run,
                quiet=quiet,
            )
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Fetch cancelled by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


async def _fetch_async(
    config_path: Path,
    users: Optional[List[str]],
    full_sync: bool,
    limit: Optional[int],
    dry_run: bool,
    quiet: bool,
):
    """Async fetch implementation."""
    if not quiet:
        console.print("[bold]Trudy 2.0 - Fetch Phase[/bold]")
        console.print()

    # Load configuration
    if not config_path.exists():
        console.print(f"[red]Config file not found: {config_path}[/red]")
        raise typer.Exit(1)

    config = load_config(str(config_path))

    # Initialize components
    state_manager = StateManager(config.storage.base_path / "state.json")
    telegram_client = TelegramClient(config.telegram)
    downloader = MediaDownloader(telegram_client)
    staging_writer = StagingWriter(config.markdown)

    # Create message fetcher
    fetcher = MessageFetcher(
        client=telegram_client,
        state_manager=state_manager,
        config=config,
        staging_writer=staging_writer,
        downloader=downloader,
    )

    # Show configuration
    if not quiet:
        console.print(f"Config: {config_path}")
        console.print(f"Mode: {'Full sync' if full_sync else 'Incremental sync'}")
        if users:
            console.print(f"Users: {', '.join(users)}")
        else:
            console.print("Users: All discovered users")
        if dry_run:
            console.print("[yellow]DRY RUN - No files will be written[/yellow]")
        console.print()

    # Fetch messages
    if not quiet:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Fetching messages from Telegram...", total=None)

            results = await fetcher.fetch_and_discover_users(full_sync=full_sync)

            progress.update(task, description="Fetch complete!")
    else:
        results = await fetcher.fetch_and_discover_users(full_sync=full_sync)

    # Filter results if specific users requested
    if users:
        results = {u: results[u] for u in users if u in results}

    # Display results
    if not quiet:
        console.print()
        _display_results(results, dry_run)


def _display_results(results: dict, dry_run: bool):
    """Display fetch results as a Rich table."""
    if not results:
        console.print("[yellow]No users found or no new messages.[/yellow]")
        return

    table = Table(title="Fetch Results" + (" (DRY RUN)" if dry_run else ""))
    table.add_column("User", style="cyan")
    table.add_column("Chat ID", style="dim")
    table.add_column("Messages Fetched", justify="right", style="green")

    total_messages = 0
    for username, (user_config, message_count) in results.items():
        table.add_row(
            username,
            str(user_config.chat_id),
            str(message_count),
        )
        total_messages += message_count

    console.print(table)
    console.print()

    # Summary
    summary = f"[bold]Total:[/bold] {len(results)} users, {total_messages} messages fetched"
    if dry_run:
        summary += " (not written)"
    console.print(summary)
