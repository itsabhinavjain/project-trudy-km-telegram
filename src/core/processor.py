"""Processing orchestration for Phase 2 (Staging to Processed).

Coordinates the processing pipeline: reads staging files, processes messages
through processor chain, writes to processed area, updates state.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.ai.tagger import Tagger
from src.core.config import Config
from src.core.logger import get_logger
from src.core.state import StateManager
from src.markdown.processed_writer import ProcessedWriter
from src.markdown.staging_reader import StagingReader
from src.processors.base import BaseProcessor, ProcessedResult
from src.telegram.fetcher import Message
from src.utils.checksum import calculate_checksum, has_file_changed

logger = get_logger(__name__)


@dataclass
class ProcessingReport:
    """Report for processing operations."""

    users_processed: int = 0
    files_processed: int = 0
    messages_processed: int = 0
    messages_skipped: int = 0  # Unchanged files
    transcriptions: int = 0
    ocr_performed: int = 0
    summaries_generated: int = 0
    tags_generated: int = 0
    links_extracted: int = 0
    errors: int = 0
    error_details: List[str] = field(default_factory=list)
    time_elapsed: float = 0.0

    def __str__(self) -> str:
        """Format as readable summary."""
        lines = [
            "Processing Report:",
            f"  Users: {self.users_processed}",
            f"  Files: {self.files_processed}",
            f"  Messages: {self.messages_processed} processed, {self.messages_skipped} skipped",
            f"  Features: {self.transcriptions} transcripts, {self.ocr_performed} OCR, "
            f"{self.summaries_generated} summaries",
            f"  Enrichments: {self.tags_generated} tags, {self.links_extracted} links",
            f"  Errors: {self.errors}",
            f"  Time: {self.time_elapsed:.2f}s",
        ]
        if self.error_details:
            lines.append("  Error details:")
            for error in self.error_details[:5]:  # Show first 5
                lines.append(f"    - {error}")
            if len(self.error_details) > 5:
                lines.append(f"    ... and {len(self.error_details) - 5} more")
        return "\n".join(lines)


class MessageProcessor:
    """Orchestrate processing pipeline: staging → processed.

    This class coordinates the two-phase processing workflow:
    1. Reads staging files (written by MessageFetcher)
    2. Checks for file changes using checksums
    3. Parses messages from staging markdown
    4. Processes messages through processor chain
    5. Writes enriched markdown to processed area
    6. Updates state with checksums and counts
    """

    def __init__(
        self,
        config: Config,
        state_manager: StateManager,
        processors: List[BaseProcessor],
        staging_reader: StagingReader,
        processed_writer: ProcessedWriter,
        tagger: Optional[Tagger] = None,
    ):
        """Initialize message processor.

        Args:
            config: Application configuration
            state_manager: State manager for tracking
            processors: List of message processors (order matters!)
            staging_reader: Staging markdown parser
            processed_writer: Processed markdown writer
            tagger: Optional tagger for auto-tagging
        """
        self.config = config
        self.state_manager = state_manager
        self.processors = processors
        self.staging_reader = staging_reader
        self.processed_writer = processed_writer
        self.tagger = tagger

    async def process_pending_files(
        self,
        username: str,
        reprocess: bool = False,
        skip_options: Optional[Dict] = None,
    ) -> ProcessingReport:
        """Process pending staging files for a user.

        Args:
            username: User to process
            reprocess: Force reprocessing even if files unchanged
            skip_options: Dict with keys: transcription, ocr, summarization, tags, links

        Returns:
            Processing report with statistics
        """
        skip_options = skip_options or {}
        report = ProcessingReport()
        start_time = datetime.now()

        # Get pending files from state
        pending_files = self.state_manager.get_pending_files(username)

        if not pending_files:
            logger.info(f"No pending files for {username}")
            return report

        logger.info(f"Processing {len(pending_files)} pending file(s) for {username}")

        # Get directories
        processed_dir = self.config.storage.get_processed_dir(username)

        for staging_file_str in pending_files:
            staging_file = Path(staging_file_str)

            try:
                # Check if file exists
                if not staging_file.exists():
                    logger.warning(f"Staging file not found: {staging_file}")
                    # Remove from pending since it's gone
                    state = self.state_manager.load()
                    if username in state.users:
                        if staging_file_str in state.users[username].process_state.pending_files:
                            state.users[username].process_state.pending_files.remove(staging_file_str)
                            self.state_manager.save(state)
                    continue

                # Calculate checksum
                current_checksum = calculate_checksum(staging_file)
                stored_checksum = self.state_manager.get_file_checksum(username, staging_file_str)

                # Skip if unchanged (unless reprocess=True)
                if not reprocess and not has_file_changed(staging_file, stored_checksum):
                    logger.debug(f"Skipping unchanged file: {staging_file.name}")
                    report.messages_skipped += 1
                    continue

                # Read messages from staging
                messages = await self.staging_reader.read_file(staging_file, username)

                if not messages:
                    logger.warning(f"No messages parsed from {staging_file.name}")
                    # Still mark as processed to avoid re-checking
                    self.state_manager.mark_file_processed(
                        username, staging_file_str, current_checksum, 0
                    )
                    continue

                logger.info(f"Processing {len(messages)} message(s) from {staging_file.name}")

                # Process each message
                messages_processed = 0
                for message in messages:
                    try:
                        result = await self._process_message(message, username, skip_options)

                        # Write to processed
                        await self.processed_writer.append_entry(
                            processed_dir=processed_dir,
                            message=message,
                            processed_result=result,
                        )

                        messages_processed += 1
                        report.messages_processed += 1

                        # Update report stats
                        if result.transcript_file:
                            report.transcriptions += 1
                        if result.summary:
                            report.summaries_generated += 1
                        if result.ocr_text:
                            report.ocr_performed += 1
                        if result.tags:
                            report.tags_generated += len(result.tags)
                        if result.links:
                            report.links_extracted += len(result.links)

                    except Exception as e:
                        logger.error(f"Error processing message {message.message_id}: {e}")
                        report.errors += 1
                        report.error_details.append(f"Message {message.message_id}: {str(e)}")
                        if not self.config.processing.skip_errors:
                            raise

                # Mark file as processed
                self.state_manager.mark_file_processed(
                    username, staging_file_str, current_checksum, messages_processed
                )
                report.files_processed += 1

            except Exception as e:
                logger.error(f"Error processing staging file {staging_file}: {e}")
                report.errors += 1
                report.error_details.append(f"File {staging_file.name}: {str(e)}")
                if not self.config.processing.skip_errors:
                    raise

        report.users_processed = 1
        report.time_elapsed = (datetime.now() - start_time).total_seconds()

        logger.info(f"Completed processing for {username}: {report.messages_processed} messages")
        return report

    async def process_all_users(
        self,
        usernames: Optional[List[str]] = None,
        reprocess: bool = False,
        skip_options: Optional[Dict] = None,
    ) -> ProcessingReport:
        """Process pending files for all users.

        Args:
            usernames: Specific users to process (None = all users)
            reprocess: Force reprocessing even if files unchanged
            skip_options: Processing options to skip

        Returns:
            Combined processing report
        """
        combined_report = ProcessingReport()
        start_time = datetime.now()

        # Determine which users to process
        state = self.state_manager.load()
        if usernames:
            users_to_process = [u for u in usernames if u in state.users]
        else:
            users_to_process = list(state.users.keys())

        logger.info(f"Processing {len(users_to_process)} user(s)")

        for username in users_to_process:
            try:
                report = await self.process_pending_files(username, reprocess, skip_options)

                # Merge reports
                combined_report.files_processed += report.files_processed
                combined_report.messages_processed += report.messages_processed
                combined_report.messages_skipped += report.messages_skipped
                combined_report.transcriptions += report.transcriptions
                combined_report.ocr_performed += report.ocr_performed
                combined_report.summaries_generated += report.summaries_generated
                combined_report.tags_generated += report.tags_generated
                combined_report.links_extracted += report.links_extracted
                combined_report.errors += report.errors
                combined_report.error_details.extend(report.error_details)

            except Exception as e:
                logger.error(f"Failed to process user {username}: {e}")
                combined_report.errors += 1
                combined_report.error_details.append(f"User {username}: {str(e)}")

        combined_report.users_processed = len(users_to_process)
        combined_report.time_elapsed = (datetime.now() - start_time).total_seconds()

        logger.info(f"Processing complete: {combined_report}")
        return combined_report

    async def _process_message(
        self,
        message: Message,
        username: str,
        skip_options: Dict,
    ) -> ProcessedResult:
        """Process single message through processor chain.

        Args:
            message: Message to process
            username: Username (for directory paths)
            skip_options: Processing options to skip

        Returns:
            ProcessedResult with all metadata

        Raises:
            Exception: If no processor can handle the message
        """
        # Get directories (processors may need them)
        media_dir = self.config.storage.get_media_dir(username)
        processed_dir = self.config.storage.get_processed_dir(username)

        # Find matching processor
        processor = await self._find_processor(message)
        if not processor:
            logger.warning(
                f"No processor found for message type '{message.message_type}', "
                f"using text processor as fallback"
            )
            # Fallback to first processor (usually TextProcessor)
            processor = self.processors[0] if self.processors else None
            if not processor:
                raise ValueError(f"No processors available to handle message {message.message_id}")

        # Process message
        # Note: In v2.0, media is already downloaded by fetcher, so media_dir contains existing files
        result = await processor.process(message, media_dir, processed_dir)

        # Apply tagging (if enabled and not skipped)
        if not skip_options.get('tags', False) and self.tagger:
            result.tags = await self.tagger.generate_tags(message, result)

        return result

    async def _find_processor(self, message: Message) -> Optional[BaseProcessor]:
        """Find processor that can handle this message.

        Args:
            message: Message to process

        Returns:
            First processor that can handle the message, or None
        """
        for processor in self.processors:
            if await processor.can_process(message):
                return processor
        return None
