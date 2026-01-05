"""Utility commands - Clean staging or processed areas."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Confirm

from src.core.config import load_config
from src.core.logger import get_logger, set_log_level

console = Console()
logger = get_logger(__name__)


def _get_files_before_date(directory: Path, before_date: datetime) -> list[Path]:
    """Get all markdown files in directory modified before given date."""
    if not directory.exists():
        return []

    files = []
    for md_file in directory.rglob("*.md"):
        # Check file modification time
        mtime = datetime.fromtimestamp(md_file.stat().st_mtime)
        if mtime < before_date:
            files.append(md_file)
    return files


def _delete_files(files: list[Path], dry_run: bool = False) -> tuple[int, int]:
    """Delete files and return (success_count, error_count)."""
    success = 0
    errors = 0

    for file_path in files:
        try:
            if not dry_run:
                file_path.unlink()
            success += 1
            logger.debug(f"Deleted: {file_path}")
        except Exception as e:
            errors += 1
            logger.error(f"Failed to delete {file_path}: {e}")

    return success, errors


def clean_cmd(
    ctx: typer.Context,
    staging: bool = typer.Option(
        False,
        "--staging",
        help="Clean staging area",
    ),
    processed: bool = typer.Option(
        False,
        "--processed",
        help="Clean processed area",
    ),
    media: bool = typer.Option(
        False,
        "--media",
        help="Clean media files",
    ),
    user: Optional[str] = typer.Option(
        None,
        "--user",
        "-u",
        help="Clean specific user only",
    ),
    before: Optional[str] = typer.Option(
        None,
        "--before",
        help="Clean files before date (YYYY-MM-DD)",
    ),
    days: Optional[int] = typer.Option(
        None,
        "--days",
        help="Clean files older than N days",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview what would be deleted without actually deleting",
    ),
):
    """Clean staging, processed, or media areas.

    By default, applies the retention policy from config. You can also
    specify custom cleanup criteria with --before or --days.

    WARNING: This operation cannot be undone! Use --dry-run first.

    Examples:
        trudy clean --staging --dry-run         # Preview staging cleanup
        trudy clean --staging --days 7          # Delete staging files older than 7 days
        trudy clean --processed --before 2026-01-01  # Delete processed files before date
        trudy clean --staging --user alice      # Clean staging for specific user
        trudy clean --media --days 30           # Clean media files older than 30 days
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
        # Validate options
        if not any([staging, processed, media]):
            console.print("[red]Error: Must specify at least one of --staging, --processed, or --media[/red]")
            raise typer.Exit(code=1)

        if before and days:
            console.print("[red]Error: Cannot use both --before and --days[/red]")
            raise typer.Exit(code=1)

        # Load configuration
        config = load_config(config_path)

        # Determine cutoff date
        cutoff_date = None
        if before:
            try:
                cutoff_date = datetime.strptime(before, "%Y-%m-%d")
            except ValueError:
                console.print(f"[red]Error: Invalid date format '{before}'. Use YYYY-MM-DD[/red]")
                raise typer.Exit(code=1)
        elif days:
            cutoff_date = datetime.now() - timedelta(days=days)
        elif staging and config.storage.staging_retention.policy == "keep_days":
            # Use retention policy from config
            retention_days = config.storage.staging_retention.days
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            console.print(f"[dim]Using retention policy: keep {retention_days} days[/dim]")

        # Show header
        if not quiet:
            console.print("\n[bold cyan]Trudy 2.0 - Clean Utility[/bold cyan]\n")

        if dry_run:
            console.print("[yellow]DRY RUN - No files will be deleted[/yellow]\n")

        # Collect files to delete
        files_to_delete = []

        if staging:
            staging_dir = config.storage.base_dir / config.storage.staging_dir
            if user:
                staging_dir = staging_dir / user

            if cutoff_date:
                files = _get_files_before_date(staging_dir, cutoff_date)
            else:
                files = list(staging_dir.rglob("*.md")) if staging_dir.exists() else []

            files_to_delete.extend(files)
            console.print(f"[cyan]Staging:[/cyan] Found {len(files)} file(s) to clean")

        if processed:
            processed_dir = config.storage.base_dir / config.storage.processed_dir
            if user:
                processed_dir = processed_dir / user

            if cutoff_date:
                files = _get_files_before_date(processed_dir, cutoff_date)
            else:
                files = list(processed_dir.rglob("*.md")) if processed_dir.exists() else []

            files_to_delete.extend(files)
            console.print(f"[blue]Processed:[/blue] Found {len(files)} file(s) to clean")

        if media:
            media_dir = config.storage.base_dir / config.storage.media_dir
            if user:
                media_dir = media_dir / user

            if cutoff_date:
                # For media, check all files (not just .md)
                files = []
                if media_dir.exists():
                    for file_path in media_dir.rglob("*"):
                        if file_path.is_file():
                            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                            if mtime < cutoff_date:
                                files.append(file_path)
            else:
                files = [f for f in media_dir.rglob("*") if f.is_file()] if media_dir.exists() else []

            files_to_delete.extend(files)
            console.print(f"[magenta]Media:[/magenta] Found {len(files)} file(s) to clean")

        # Show summary
        console.print(f"\n[bold]Total files to delete: {len(files_to_delete)}[/bold]")

        if not files_to_delete:
            console.print("[green]Nothing to clean![/green]")
            return

        # Show sample of files
        if verbose and files_to_delete:
            console.print("\n[dim]Sample files:[/dim]")
            for file_path in files_to_delete[:10]:
                console.print(f"  [dim]{file_path}[/dim]")
            if len(files_to_delete) > 10:
                console.print(f"  [dim]... and {len(files_to_delete) - 10} more[/dim]")

        # Confirm before deleting (unless dry run)
        if not dry_run:
            if quiet:
                # Auto-confirm in quiet mode
                confirmed = True
            else:
                console.print()
                confirmed = Confirm.ask(
                    f"[yellow]Delete {len(files_to_delete)} file(s)?[/yellow]",
                    default=False,
                )

            if not confirmed:
                console.print("[yellow]Cancelled[/yellow]")
                return

        # Delete files
        success, errors = _delete_files(files_to_delete, dry_run=dry_run)

        # Show results
        if dry_run:
            console.print(f"\n[green]Would delete {success} file(s)[/green]")
        else:
            console.print(f"\n[green]Successfully deleted {success} file(s)[/green]")
            if errors:
                console.print(f"[red]Failed to delete {errors} file(s)[/red]")

    except Exception as e:
        logger.error(f"Clean operation failed: {e}")
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)
