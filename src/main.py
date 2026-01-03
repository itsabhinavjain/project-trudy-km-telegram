"""Main CLI entry point for Trudy Telegram system."""

import asyncio
import sys
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.ai.claude_summarizer import ClaudeSummarizer
from src.ai.ollama_summarizer import OllamaSummarizer
from src.ai.transcriber import Transcriber
from src.core.config import Config, load_config
from src.core.logger import get_logger, setup_logging
from src.core.state import StateManager
from src.markdown.writer import MarkdownWriter
from src.processors.audio_video import AudioVideoProcessor
from src.processors.link import LinkProcessor
from src.processors.media import MediaProcessor
from src.processors.text import TextProcessor
from src.processors.youtube import YouTubeProcessor
from src.telegram.client import TelegramClient
from src.telegram.downloader import MediaDownloader
from src.telegram.fetcher import Message, MessageFetcher
from src.utils.article_extractor import ArticleExtractor
from src.utils.youtube_utils import YouTubeUtils

console = Console()
logger = None  # Will be initialized after config load


async def process_messages(
    config: Config,
    messages: List[Message],
    username: str,
) -> dict:
    """Process messages for a user.

    Args:
        config: Application configuration
        messages: List of messages to process
        username: Username being processed

    Returns:
        Statistics dictionary
    """
    if not messages:
        return {
            "total": 0,
            "processed": 0,
            "media": 0,
            "transcriptions": 0,
            "summaries": 0,
        }

    logger.info(f"Processing {len(messages)} messages for {username}")

    # Initialize components
    client = TelegramClient(config.telegram)
    downloader = MediaDownloader(client)
    transcriber = Transcriber(config.transcription)
    article_extractor = ArticleExtractor()
    youtube_utils = YouTubeUtils()
    markdown_writer = MarkdownWriter(config.markdown)

    # Initialize summarizer based on config
    summarizer = None
    if config.summarization.enabled:
        if config.summarization.provider == "ollama":
            summarizer = OllamaSummarizer(config.summarization)
        elif config.summarization.provider == "claude":
            summarizer = ClaudeSummarizer(config.summarization)

    # Initialize processors
    processors = [
        TextProcessor(config),
        MediaProcessor(config, downloader),
        AudioVideoProcessor(config, downloader, transcriber, summarizer),
        LinkProcessor(config, article_extractor, summarizer),
        YouTubeProcessor(config, youtube_utils, transcriber, summarizer),
    ]

    # Get directories
    notes_dir = config.storage.get_user_notes_dir(username)
    media_dir = config.storage.get_user_media_dir(username)

    # Process each message
    stats = {
        "total": len(messages),
        "processed": 0,
        "media": 0,
        "transcriptions": 0,
        "summaries": 0,
        "errors": 0,
    }

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Processing messages for {username}...", total=len(messages))

        for message in messages:
            try:
                # Find appropriate processor
                processor = None
                for p in processors:
                    if await p.can_process(message):
                        processor = p
                        break

                if not processor:
                    logger.warning(f"No processor for message {message.message_id}")
                    continue

                # Process message
                result = await processor.process(message, media_dir, notes_dir)

                # Write to markdown
                await markdown_writer.append_entry(notes_dir, message, result.markdown_content)

                # Update stats
                stats["processed"] += 1
                if result.media_files:
                    stats["media"] += len(result.media_files)
                if result.transcript_file:
                    stats["transcriptions"] += 1
                if result.summary:
                    stats["summaries"] += 1

            except Exception as e:
                logger.error(f"Failed to process message {message.message_id}: {e}")
                stats["errors"] += 1

                if not config.processing.skip_errors:
                    raise

            progress.advance(task)

    await client.close()

    return stats


async def main_async(
    config_path: str,
    full_sync: bool,
    user_filter: Optional[str],
    dry_run: bool,
    no_summarize: bool,
    verbose: bool,
    discover_users: bool = False,
) -> int:
    """Main async function.

    Args:
        config_path: Path to configuration file
        full_sync: If True, fetch all historical messages
        user_filter: Optional username to process only that user
        dry_run: If True, don't write any files
        no_summarize: If True, skip summarization
        verbose: Enable verbose logging
        discover_users: If True, only discover and list users without processing

    Returns:
        Exit code
    """
    global logger

    # Load configuration
    try:
        config = load_config(config_path)
    except Exception as e:
        console.print(f"[red]Failed to load configuration: {e}[/red]")
        return 1

    # Adjust config based on flags
    if no_summarize:
        config.summarization.enabled = False
    if verbose:
        config.logging.level = "DEBUG"

    # Setup logging
    logger = setup_logging(config.logging)

    console.print("[bold cyan]Trudy Telegram Note-Taking System[/bold cyan]\n")

    # Initialize state manager
    state_file = Path(config.storage.base_dir) / "state.json"
    state_manager = StateManager(state_file)
    state_manager.load()

    # Initialize Telegram client and fetcher
    client = TelegramClient(config.telegram)
    fetcher = MessageFetcher(client, state_manager)

    try:
        # Handle --discover-users flag
        if discover_users:
            console.print("[bold]Discovering all users...[/bold]\n")

            # Fetch messages and discover users
            discovered = await fetcher.fetch_and_discover_users(full_sync=True)

            if not discovered:
                console.print("[yellow]No users found[/yellow]")
                return 0

            # Display discovered users
            console.print(f"[bold green]Discovered {len(discovered)} users:[/bold green]\n")

            for username, (user_config, messages) in discovered.items():
                user_state = state_manager.get_user_state(username)

                console.print(f"  [cyan]• {username}[/cyan]")
                console.print(f"    Chat ID: {user_config.chat_id}")
                if user_config.phone:
                    console.print(f"    Phone: {user_config.phone}")
                if user_state:
                    console.print(f"    Total messages: {user_state.total_messages}")
                    if user_state.first_message_time:
                        console.print(f"    First message: {user_state.first_message_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    if user_state.last_fetch_time:
                        console.print(f"    Last fetch: {user_state.last_fetch_time.strftime('%Y-%m-%d %H:%M:%S')}")
                console.print()

            # Update state for any newly discovered users
            for username, (user_config, messages) in discovered.items():
                user_state = state_manager.get_user_state(username)
                if not user_state:
                    # New user - save to state
                    state_manager.update_user_state(
                        username=username,
                        chat_id=user_config.chat_id,
                        phone=user_config.phone,
                        message_id=None,
                        message_count=0,
                    )
                    console.print(f"[green]✓ Added new user to state: {username}[/green]")

            console.print(f"\n[bold green]User discovery complete![/bold green]")
            return 0

        # Determine if we're using auto-discovery or configured users
        use_auto_discovery = len(config.users) == 0

        if use_auto_discovery:
            console.print("[bold]Auto-discovering users from bot messages...[/bold]")

            # Fetch messages and discover users
            discovered = await fetcher.fetch_and_discover_users(full_sync=full_sync)

            # Filter by user if specified
            if user_filter:
                if user_filter not in discovered:
                    console.print(f"[red]User not found: {user_filter}[/red]")
                    return 1
                discovered = {user_filter: discovered[user_filter]}

            total_new = sum(len(messages) for _, messages in discovered.values())
            console.print(f"Found {len(discovered)} users with {total_new} new messages\n")

            if total_new == 0:
                console.print("[green]No new messages to process[/green]")
                return 0

            # Process messages for each discovered user
            overall_stats = {
                "total": 0,
                "processed": 0,
                "media": 0,
                "transcriptions": 0,
                "summaries": 0,
                "errors": 0,
            }

            for username, (user_config, messages) in discovered.items():
                if not messages:
                    continue

                console.print(f"\n[bold]Processing {username}...[/bold]")

                if dry_run:
                    console.print(f"[yellow]DRY RUN: Would process {len(messages)} messages[/yellow]")
                    continue

                stats = await process_messages(config, messages, username)

                # Update state
                if messages:
                    last_message = max(messages, key=lambda m: m.message_id)
                    state_manager.update_user_state(
                        username=username,
                        chat_id=user_config.chat_id,
                        phone=user_config.phone,
                        message_id=last_message.message_id,
                        message_count=len(messages),
                        first_message_time=messages[0].timestamp if messages else None,
                    )

                # Update overall stats
                for key in overall_stats:
                    overall_stats[key] += stats.get(key, 0)

                console.print(f"  Processed: {stats['processed']}/{stats['total']}")
                console.print(f"  Media: {stats['media']}")
                console.print(f"  Transcriptions: {stats['transcriptions']}")
                console.print(f"  Summaries: {stats['summaries']}")
                if stats["errors"] > 0:
                    console.print(f"  [yellow]Errors: {stats['errors']}[/yellow]")

        else:
            # Using configured users
            console.print("[bold]Using configured users...[/bold]")

            # Filter users if specified
            users = config.users
            if user_filter:
                users = [u for u in users if u.username == user_filter]
                if not users:
                    console.print(f"[red]User not found: {user_filter}[/red]")
                    return 1

            # Fetch messages
            console.print("[bold]Fetching messages...[/bold]")
            all_messages = await fetcher.fetch_all_users(users, full_sync=full_sync)

            total_new = sum(len(msgs) for msgs in all_messages.values())
            console.print(f"Found {total_new} new messages\n")

            if total_new == 0:
                console.print("[green]No new messages to process[/green]")
                return 0

            # Process messages for each user
            overall_stats = {
                "total": 0,
                "processed": 0,
                "media": 0,
                "transcriptions": 0,
                "summaries": 0,
                "errors": 0,
            }

            for user in users:
                messages = all_messages.get(user.username, [])
                if not messages:
                    continue

                console.print(f"\n[bold]Processing {user.username}...[/bold]")

                if dry_run:
                    console.print(f"[yellow]DRY RUN: Would process {len(messages)} messages[/yellow]")
                    continue

                stats = await process_messages(config, messages, user.username)

                # Update state
                if messages:
                    last_message = max(messages, key=lambda m: m.message_id)
                    state_manager.update_user_state(
                        username=user.username,
                        chat_id=user.chat_id,
                        phone=user.phone,
                        message_id=last_message.message_id,
                        message_count=len(messages),
                        first_message_time=messages[0].timestamp if messages else None,
                    )

                # Update overall stats
                for key in overall_stats:
                    overall_stats[key] += stats.get(key, 0)

                console.print(f"  Processed: {stats['processed']}/{stats['total']}")
                console.print(f"  Media: {stats['media']}")
                console.print(f"  Transcriptions: {stats['transcriptions']}")
                console.print(f"  Summaries: {stats['summaries']}")
                if stats["errors"] > 0:
                    console.print(f"  [yellow]Errors: {stats['errors']}[/yellow]")

        # Update global statistics
        state_manager.increment_statistics(
            messages=overall_stats["processed"],
            media=overall_stats["media"],
            transcriptions=overall_stats["transcriptions"],
            summaries=overall_stats["summaries"],
        )

        # Print summary
        console.print(f"\n[bold green]Complete![/bold green]")
        console.print(f"Total processed: {overall_stats['processed']}/{overall_stats['total']}")

        return 0

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        console.print(f"\n[red]Error: {e}[/red]")
        return 1
    finally:
        await client.close()


@click.command()
@click.option(
    "--config",
    "-c",
    default="config/config.yaml",
    help="Path to configuration file",
    type=click.Path(exists=True),
)
@click.option(
    "--full",
    is_flag=True,
    help="Fetch all historical messages (not just new ones)",
)
@click.option(
    "--user",
    "-u",
    help="Process only messages for this user",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Don't write any files (preview mode)",
)
@click.option(
    "--no-summarize",
    is_flag=True,
    help="Skip summarization (faster processing)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
@click.option(
    "--discover-users",
    is_flag=True,
    help="Discover and list all users without processing messages",
)
def cli(
    config: str,
    full: bool,
    user: Optional[str],
    dry_run: bool,
    no_summarize: bool,
    verbose: bool,
    discover_users: bool,
):
    """Trudy Telegram Note-Taking System.

    Fetch messages from Telegram bot and process them into organized markdown notes.
    """
    exit_code = asyncio.run(
        main_async(
            config_path=config,
            full_sync=full,
            user_filter=user,
            dry_run=dry_run,
            no_summarize=no_summarize,
            verbose=verbose,
            discover_users=discover_users,
        )
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    cli()
