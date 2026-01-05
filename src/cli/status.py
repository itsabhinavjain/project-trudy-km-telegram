"""Status and info commands - Show sync status and system information."""

import subprocess
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.core.config import load_config
from src.core.logger import get_logger, set_log_level
from src.core.state import StateManager

console = Console()
logger = get_logger(__name__)


def status_cmd(
    ctx: typer.Context,
    user: Optional[str] = typer.Option(
        None,
        "--user",
        "-u",
        help="Show status for specific user only",
    ),
):
    """Show sync status for users.

    Displays the current state of fetching and processing for all users
    or a specific user. Shows last fetch time, last process time, and
    pending files.

    Examples:
        trudy status                    # Show all users
        trudy status --user alice       # Show specific user
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

    try:
        # Load configuration and state
        config = load_config(config_path)
        state_manager = StateManager(config.storage.base_dir / "state.json")

        # Get users to display
        all_users = state_manager.get_all_users()

        if user:
            if user not in all_users:
                console.print(f"[red]User '{user}' not found in state[/red]")
                raise typer.Exit(code=1)
            users_to_show = [user]
        else:
            users_to_show = all_users

        if not users_to_show:
            console.print("[yellow]No users found. Run 'trudy discover' or 'trudy sync' first.[/yellow]")
            return

        # Create status table
        table = Table(title="Sync Status", show_header=True)
        table.add_column("User", style="cyan")
        table.add_column("Chat ID", style="magenta")
        table.add_column("Fetched", justify="right", style="green")
        table.add_column("Processed", justify="right", style="blue")
        table.add_column("Pending", justify="right", style="yellow")
        table.add_column("Last Fetch", style="dim")
        table.add_column("Last Process", style="dim")

        for username in users_to_show:
            user_state = state_manager.get_user_state(username)

            if user_state:
                # Format data
                chat_id = str(user_state.chat_id) if user_state.chat_id else "N/A"
                fetched = str(user_state.fetch_state.total_messages_fetched)
                processed = str(user_state.process_state.total_messages_processed)
                pending = str(len(user_state.process_state.pending_files))

                last_fetch = (
                    user_state.fetch_state.last_fetch_time.strftime("%Y-%m-%d %H:%M")
                    if user_state.fetch_state.last_fetch_time
                    else "Never"
                )
                last_process = (
                    user_state.process_state.last_process_time.strftime("%Y-%m-%d %H:%M")
                    if user_state.process_state.last_process_time
                    else "Never"
                )

                table.add_row(
                    username,
                    chat_id,
                    fetched,
                    processed,
                    pending,
                    last_fetch,
                    last_process,
                )

        console.print(table)
        console.print(f"\n[green]Total: {len(users_to_show)} user(s)[/green]")

    except Exception as e:
        logger.error(f"Failed to show status: {e}")
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


def info_cmd(
    ctx: typer.Context,
):
    """Show system info and configuration.

    Displays information about:
    - Configuration paths and settings
    - Available AI models (Ollama, Tesseract)
    - Storage statistics
    - System dependencies

    Examples:
        trudy info                      # Show all info
        trudy info -v                   # Verbose output
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

    try:
        # Load configuration
        config = load_config(config_path)

        console.print("\n[bold cyan]Trudy 2.0 - System Information[/bold cyan]\n")

        # Configuration section
        config_info = f"""[bold]Configuration:[/bold]
Config File: {config_path}
Base Directory: {config.storage.base_dir}
Timezone: {config.markdown.timezone}
Wikilink Style: {config.markdown.wikilink_style}
"""
        console.print(Panel(config_info, title="Configuration", border_style="cyan"))

        # AI Features section
        ai_info = f"""[bold]AI Features:[/bold]
Transcription: {'✓ Enabled' if config.transcription.enabled else '✗ Disabled'} ({config.transcription.provider})
Summarization: {'✓ Enabled' if config.summarization.enabled else '✗ Disabled'} ({config.summarization.provider})
OCR: {'✓ Enabled' if config.ocr.enabled else '✗ Disabled'} ({config.ocr.provider})
Tagging: {'✓ Enabled' if config.tagging.enabled else '✗ Disabled'}
"""
        console.print(Panel(ai_info, title="AI Features", border_style="green"))

        # Check Ollama availability
        ollama_status = "Not checked"
        if config.transcription.enabled and config.transcription.provider == "ollama":
            try:
                result = subprocess.run(
                    ["ollama", "list"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    models = [line.split()[0] for line in result.stdout.strip().split("\n")[1:]]
                    ollama_status = f"✓ Running ({len(models)} models available)"
                else:
                    ollama_status = "✗ Not running"
            except (subprocess.TimeoutExpired, FileNotFoundError):
                ollama_status = "✗ Not installed"

        # Check Tesseract availability
        tesseract_status = "Not checked"
        if config.ocr.enabled and config.ocr.provider == "tesseract":
            try:
                result = subprocess.run(
                    ["tesseract", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    version = result.stdout.split("\n")[0]
                    tesseract_status = f"✓ {version}"
                else:
                    tesseract_status = "✗ Not available"
            except (subprocess.TimeoutExpired, FileNotFoundError):
                tesseract_status = "✗ Not installed"

        # System dependencies section
        deps_info = f"""[bold]System Dependencies:[/bold]
Ollama: {ollama_status}
Tesseract: {tesseract_status}
"""
        console.print(Panel(deps_info, title="Dependencies", border_style="blue"))

        # Storage statistics
        staging_dir = config.storage.base_dir / config.storage.staging_dir
        processed_dir = config.storage.base_dir / config.storage.processed_dir
        media_dir = config.storage.base_dir / config.storage.media_dir

        staging_files = len(list(staging_dir.rglob("*.md"))) if staging_dir.exists() else 0
        processed_files = len(list(processed_dir.rglob("*.md"))) if processed_dir.exists() else 0
        media_files = len(list(media_dir.rglob("*"))) if media_dir.exists() else 0

        storage_info = f"""[bold]Storage:[/bold]
Staging Files: {staging_files}
Processed Files: {processed_files}
Media Files: {media_files}
"""
        console.print(Panel(storage_info, title="Storage Statistics", border_style="magenta"))

        # State information
        state_file = config.storage.base_dir / "state.json"
        if state_file.exists():
            state_manager = StateManager(state_file)
            users = state_manager.get_all_users()
            state_info = f"""[bold]State:[/bold]
Users Tracked: {len(users)}
State File: {state_file}
"""
            console.print(Panel(state_info, title="State", border_style="yellow"))

    except Exception as e:
        logger.error(f"Failed to show info: {e}")
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)
