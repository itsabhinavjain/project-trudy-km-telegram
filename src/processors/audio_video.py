"""Audio and video message processor with transcription support."""

from pathlib import Path
from typing import Optional

from src.ai.transcriber import Transcriber, TranscriptionError
from src.core.logger import get_logger
from src.markdown.formatter import format_wikilink, format_transcript_link
from src.processors.base import BaseProcessor, ProcessedResult
from src.telegram.downloader import MediaDownloader
from src.telegram.fetcher import Message
from src.utils.file_utils import generate_transcript_filename

logger = get_logger(__name__)


class AudioVideoProcessor(BaseProcessor):
    """Processes audio and video messages with transcription."""

    def __init__(
        self,
        config,
        downloader: MediaDownloader,
        transcriber: Transcriber,
        summarizer: Optional[object] = None,
    ):
        """Initialize audio/video processor.

        Args:
            config: Application configuration
            downloader: Media downloader instance
            transcriber: Transcriber instance
            summarizer: Optional summarizer instance
        """
        super().__init__(config)
        self.downloader = downloader
        self.transcriber = transcriber
        self.summarizer = summarizer

    async def can_process(self, message: Message) -> bool:
        """Check if this is an audio or video message.

        Args:
            message: Message to check

        Returns:
            True if message is audio or video
        """
        return message.message_type in ["audio", "video", "voice"]

    async def process(
        self,
        message: Message,
        media_dir: Path,
        notes_dir: Path,
    ) -> ProcessedResult:
        """Process an audio or video message.

        Args:
            message: Message to process
            media_dir: Directory for media files
            notes_dir: Directory for notes

        Returns:
            Processed result with markdown content
        """
        logger.debug(f"Processing {message.message_type} message {message.message_id}")

        # Download media file
        media_file = await self.downloader.download_media(message, media_dir)

        if not media_file:
            logger.error(f"Failed to download {message.message_type} for message {message.message_id}")
            return ProcessedResult(
                markdown_content=f"**{message.message_type.capitalize()} - Download Failed**\n\n",
                metadata={"type": message.message_type, "error": "download_failed"},
            )

        # Determine header
        type_labels = {
            "audio": "Audio Recording",
            "video": "Video Note",
            "voice": "Voice Message",
        }
        header = type_labels.get(message.message_type, "Media")

        # Build markdown content
        content_parts = []
        content_parts.append(self._format_header(message, header))

        # Add wikilink to media file
        wikilink = format_wikilink(
            filename=media_file.name,
            caption=message.caption,
            style=self.config.markdown.wikilink_style,
            is_embed=True,
        )
        content_parts.append(f"{wikilink}\n\n")

        # Transcribe audio/video
        transcript_file = None
        transcript_text = None
        summary = None

        try:
            transcript_text = await self.transcriber.transcribe_file(media_file)

            # Save transcript to file
            transcript_filename = generate_transcript_filename(media_file.name)
            transcript_file = media_dir / transcript_filename

            with open(transcript_file, "w", encoding="utf-8") as f:
                f.write(transcript_text)

            logger.info(f"Saved transcript to {transcript_file}")

            # Add transcript link
            content_parts.append(
                format_transcript_link(
                    transcript_filename,
                    style=self.config.markdown.wikilink_style,
                )
            )

            # Generate summary if summarizer is available
            if self.summarizer and self.config.summarization.enabled:
                try:
                    prompt = self.config.summarization.prompts.video_summary if message.message_type == "video" else self.config.summarization.prompts.audio_summary
                    summary = await self.summarizer.summarize(
                        transcript_text,
                        prompt=prompt,
                    )

                    if summary:
                        content_parts.append(self._format_summary(summary))

                except Exception as e:
                    logger.warning(f"Failed to generate summary: {e}")

        except TranscriptionError as e:
            logger.warning(f"Transcription failed: {e}")
            content_parts.append(f"*Transcription unavailable: {str(e)}*\n\n")

        markdown_content = "".join(content_parts)

        return ProcessedResult(
            markdown_content=markdown_content,
            media_files=[media_file],
            transcript_file=transcript_file,
            summary=summary,
            metadata={
                "type": message.message_type,
                "filename": media_file.name,
                "has_transcript": transcript_file is not None,
                "has_summary": summary is not None,
            },
        )
