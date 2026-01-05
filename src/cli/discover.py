"""Discover command - Find users who have messaged the bot."""

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from src.core.config import load_config
from src.core.logger import get_logger, set_log_level
from src.telegram.client import TelegramClient

console = Console()
logger = get_logger(__name__)


async def _discover_users_async(
    config_path: Path,
    full: bool,
    refresh: bool,
    verbose: bool,
) -> None:
    """Async implementation of user discovery."""
    # Load configuration
    config = load_config(config_path)

    # Initialize Telegram client
    client = TelegramClient(
        bot_token=config.telegram.bot_token,
        timeout=config.telegram.timeout,
        max_retries=config.telegram.max_retries,
    )

    try:
        # Get updates from Telegram
        if full:
            logger.info("Scanning all historical messages for users...")
            offset = -1  # Get all historical updates
        else:
            logger.info("Scanning recent messages for users...")
            offset = 0  # Get recent updates only

        updates = await client.get_updates(offset=offset, limit=100)

        # Extract unique users
        users = {}
        for update in updates:
            if "message" in update:
                msg = update["message"]
                chat = msg.get("chat", {})
                from_user = msg.get("from", {})

                chat_id = chat.get("id")
                username = from_user.get("username") or from_user.get("first_name", "unknown")
                first_name = from_user.get("first_name", "")
                last_name = from_user.get("last_name", "")
                phone = from_user.get("phone_number")

                if chat_id and chat_id not in users:
                    users[chat_id] = {
                        "chat_id": chat_id,
                        "username": username,
                        "first_name": first_name,
                        "last_name": last_name,
                        "phone": phone,
                    }

        # Display results
        if not users:
            console.print("[yellow]No users found. Make sure someone has messaged your bot.[/yellow]")
            console.print("\n[dim]Tip: Send a message to your bot on Telegram and try again.[/dim]")
            return

        # Create table
        table = Table(title="Discovered Users", show_header=True)
        table.add_column("Username", style="cyan")
        table.add_column("Chat ID", style="magenta")
        table.add_column("Name", style="green")
        table.add_column("Phone", style="blue")

        for user_data in users.values():
            full_name = f"{user_data['first_name']} {user_data['last_name']}".strip() or "N/A"
            phone = user_data["phone"] or "N/A"
            table.add_row(
                user_data["username"],
                str(user_data["chat_id"]),
                full_name,
                phone,
            )

        console.print(table)
        console.print(f"\n[green]Total: {len(users)} user(s) discovered[/green]")

        if not full:
            console.print("\n[dim]Tip: Use --full to scan all historical messages[/dim]")

    except Exception as e:
        logger.error(f"Failed to discover users: {e}")
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


def discover_cmd(
    ctx: typer.Context,
    full: bool = typer.Option(
        False,
        "--full",
        help="Scan all historical messages (slower but more complete)",
    ),
    refresh: bool = typer.Option(
        False,
        "--refresh",
        help="Re-scan and update user list",
    ),
):
    """Discover users who have messaged the bot.

    This command scans Telegram messages to find users who have
    interacted with your bot. By default, it scans recent messages.
    Use --full to scan the entire message history.

    Examples:
        trudy discover                  # Scan recent messages
        trudy discover --full           # Scan all history
        trudy discover --full -v        # Verbose output
    """
    # Get context options
    config_path = ctx.obj["config_path"]
    verbose = ctx.obj["verbose"]
    quiet = ctx.obj["quiet"]

    # Set log level
    if verbose:
        set_log_level("DEBUG")
    elif quiet:
        set_log_level("ERROR")

    # Show header
    if not quiet:
        console.print("\n[bold cyan]Trudy 2.0 - User Discovery[/bold cyan]\n")

    # Run async discovery
    try:
        asyncio.run(_discover_users_async(config_path, full, refresh, verbose))
    except KeyboardInterrupt:
        console.print("\n[yellow]Discovery cancelled by user[/yellow]")
        raise typer.Exit(code=130)
