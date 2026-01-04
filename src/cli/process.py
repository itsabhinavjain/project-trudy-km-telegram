"""Process command - Process staging files into enriched markdown.

This implements Phase 2 of the two-phase workflow: Staging → Processed
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from src.ai.ocr import OCRManager
from src.ai.tagger import Tagger
from src.core.config import load_config
from src.core.logger import get_logger, setup_logging
from src.core.processor import MessageProcessor
from src.core.state import StateManager
from src.markdown.processed_writer import ProcessedWriter
from src.markdown.staging_reader import StagingReader

console = Console()
logger = get_logger(__name__)


def process_cmd(
    ctx: typer.Context,
    users: Optional[List[str]] = typer.Argument(
        None,
        help="Specific users to process (usernames). Leave empty for all users.",
    ),
    all: bool = typer.Option(
        True,
        "--all",
        help="Process all users",
    ),
    user: Optional[List[str]] = typer.Option(
        None,
        "--user",
        "-u",
        help="Process specific user (can be used multiple times)",
    ),
    date: Optional[str] = typer.Option(
        None,
        "--date",
        help="Process specific date only (YYYY-MM-DD)",
    ),
    skip_transcription: bool = typer.Option(
        False,
        "--skip-transcription",
        help="Skip audio/video transcription",
    ),
    skip_ocr: bool = typer.Option(
        False,
        "--skip-ocr",
        help="Skip OCR text extraction from images",
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
    skip_links: bool = typer.Option(
        False,
        "--skip-links",
        help="Skip link metadata extraction",
    ),
    reprocess: bool = typer.Option(
        False,
        "--reprocess",
        help="Force reprocessing even if files haven't changed",
    ),
    workers: int = typer.Option(
        3,
        "--workers",
        "-w",
        help="Number of parallel processing workers (not yet implemented)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview what would be processed without writing files",
    ),
):
    """Process staging files and generate enriched markdown.

    This command implements Phase 2 of the two-phase workflow:
    - Reads pending staging files (or files that changed)
    - Parses messages from staging markdown
    - Processes through processor chain
    - Applies AI features (transcription, OCR, summarization, tagging)
    - Extracts link metadata
    - Writes enriched markdown with YAML metadata
    - Updates process_state with checksums

    Examples:
        # Process pending files for all users
        trudy process

        # Process specific user
        trudy process --user alice

        # Process without AI features (faster)
        trudy process --skip-transcription --skip-ocr --skip-summarization

        # Force reprocess all files
        trudy process --reprocess

        # Process specific date
        trudy process --date 2026-01-04

        # Preview without writing
        trudy process --dry-run
    """
    # Get context
    config_path = ctx.obj.get("config_path", Path("config/config.yaml"))
    verbose = ctx.obj.get("verbose", False)
    quiet = ctx.obj.get("quiet", False)

    # Setup logging
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level=log_level)

    # Determine which users to process
    users_to_process = None
    if user:  # --user option takes precedence
        users_to_process = user
    elif users:  # Positional arguments
        users_to_process = users
    elif not all:
        console.print("[yellow]No users specified. Use --all to process for all users.[/yellow]")
        raise typer.Exit(1)

    # Validate date format if provided
    if date:
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            console.print(f"[red]Invalid date format: {date}. Use YYYY-MM-DD[/red]")
            raise typer.Exit(1)

    # Build skip options
    skip_options = {
        "transcription": skip_transcription,
        "ocr": skip_ocr,
        "summarization": skip_summarization,
        "tags": skip_tags,
        "links": skip_links,
    }

    try:
        # Run async processing
        asyncio.run(
            _process_async(
                config_path=config_path,
                users=users_to_process,
                date=date,
                skip_options=skip_options,
                reprocess=reprocess,
                workers=workers,
                dry_run=dry_run,
                quiet=quiet,
            )
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Processing cancelled by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


async def _process_async(
    config_path: Path,
    users: Optional[List[str]],
    date: Optional[str],
    skip_options: dict,
    reprocess: bool,
    workers: int,
    dry_run: bool,
    quiet: bool,
):
    """Async processing implementation."""
    if not quiet:
        console.print("[bold]Trudy 2.0 - Process Phase[/bold]")
        console.print()

    # Load configuration
    if not config_path.exists():
        console.print(f"[red]Config file not found: {config_path}[/red]")
        raise typer.Exit(1)

    config = load_config(str(config_path))

    # Initialize components
    state_manager = StateManager(config.storage.base_path / "state.json")
    staging_reader = StagingReader(config.markdown)
    processed_writer = ProcessedWriter(config.markdown)

    # Initialize AI components
    ocr_manager = None
    if not skip_options["ocr"] and config.ocr.enabled:
        try:
            ocr_manager = OCRManager(config.ocr)
        except Exception as e:
            logger.warning(f"Failed to initialize OCR: {e}")

    tagger = None
    if not skip_options["tags"] and config.tagging.enabled:
        tagger = Tagger(config.tagging)

    # Initialize processors
    # Note: For now, we'll create a minimal processor setup
    # In full implementation, we'd initialize all processors from src/processors/
    processors = []  # TODO: Initialize processor chain

    # Create message processor
    processor = MessageProcessor(
        config=config,
        state_manager=state_manager,
        processors=processors,
        staging_reader=staging_reader,
        processed_writer=processed_writer,
        tagger=tagger,
    )

    # Show configuration
    if not quiet:
        console.print(f"Config: {config_path}")
        console.print(f"Mode: {'Reprocess all' if reprocess else 'Process changed files only'}")
        if users:
            console.print(f"Users: {', '.join(users)}")
        else:
            console.print("Users: All users with pending files")
        if date:
            console.print(f"Date filter: {date}")

        # Show enabled features
        enabled = []
        if not skip_options["transcription"]:
            enabled.append("transcription")
        if not skip_options["ocr"] and ocr_manager:
            enabled.append("OCR")
        if not skip_options["summarization"]:
            enabled.append("summarization")
        if not skip_options["tags"] and tagger:
            enabled.append("tagging")
        if not skip_options["links"]:
            enabled.append("links")

        if enabled:
            console.print(f"Features: {', '.join(enabled)}")
        else:
            console.print("Features: None (all skipped)")

        if dry_run:
            console.print("[yellow]DRY RUN - No files will be written[/yellow]")
        console.print()

    # Process messages
    if not quiet:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Processing messages...", total=None)

            report = await processor.process_all_users(
                usernames=users,
                reprocess=reprocess,
                skip_options=skip_options,
            )

            progress.update(task, description="Processing complete!")
    else:
        report = await processor.process_all_users(
            usernames=users,
            reprocess=reprocess,
            skip_options=skip_options,
        )

    # Display results
    if not quiet:
        console.print()
        _display_results(report, dry_run)

    # Exit with error code if there were errors
    if report.errors > 0:
        raise typer.Exit(1)


def _display_results(report, dry_run: bool):
    """Display processing results."""
    console.print("[bold]Processing Report[/bold]" + (" (DRY RUN)" if dry_run else ""))
    console.print()

    # Stats table
    table = Table(show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="green")

    table.add_row("Users processed", str(report.users_processed))
    table.add_row("Files processed", str(report.files_processed))
    table.add_row("Messages processed", str(report.messages_processed))
    table.add_row("Messages skipped", str(report.messages_skipped))
    table.add_row("", "")  # Spacer
    table.add_row("Transcriptions", str(report.transcriptions))
    table.add_row("OCR performed", str(report.ocr_performed))
    table.add_row("Summaries generated", str(report.summaries_generated))
    table.add_row("Tags generated", str(report.tags_generated))
    table.add_row("Links extracted", str(report.links_extracted))
    table.add_row("", "")  # Spacer
    table.add_row("Errors", str(report.errors), style="red" if report.errors > 0 else "green")
    table.add_row("Time elapsed", f"{report.time_elapsed:.2f}s")

    console.print(table)

    # Show error details if any
    if report.error_details:
        console.print()
        console.print("[bold red]Errors:[/bold red]")
        for error in report.error_details[:10]:  # Show first 10
            console.print(f"  [red]•[/red] {error}")
        if len(report.error_details) > 10:
            console.print(f"  [dim]... and {len(report.error_details) - 10} more[/dim]")
