"""YouTube video processor."""

from pathlib import Path
from typing import Optional

from src.ai.transcriber import Transcriber
from src.core.logger import get_logger
from src.markdown.formatter import extract_urls, format_transcript_link, is_youtube_url
from src.processors.base import BaseProcessor, ProcessedResult
from src.telegram.fetcher import Message
from src.utils.file_utils import generate_youtube_transcript_filename
from src.utils.youtube_utils import YouTubeUtils

logger = get_logger(__name__)


class YouTubeProcessor(BaseProcessor):
    """Processes YouTube video links."""

    def __init__(
        self,
        config,
        youtube_utils: YouTubeUtils,
        transcriber: Transcriber,
        summarizer: Optional[object] = None,
    ):
        """Initialize YouTube processor.

        Args:
            config: Application configuration
            youtube_utils: YouTube utilities instance
            transcriber: Transcriber instance
            summarizer: Optional summarizer instance
        """
        super().__init__(config)
        self.youtube_utils = youtube_utils
        self.transcriber = transcriber
        self.summarizer = summarizer

    async def can_process(self, message: Message) -> bool:
        """Check if this is a YouTube link message.

        Args:
            message: Message to check

        Returns:
            True if message contains YouTube link
        """
        if message.message_type != "link" or not message.text:
            return False

        # Extract URLs
        urls = extract_urls(message.text)
        if not urls:
            return False

        # Check if any URL is a YouTube link
        return any(is_youtube_url(url) for url in urls)

    async def process(
        self,
        message: Message,
        media_dir: Path,
        notes_dir: Path,
    ) -> ProcessedResult:
        """Process a YouTube video link.

        Args:
            message: Message to process
            media_dir: Directory for media files
            notes_dir: Directory for notes

        Returns:
            Processed result with markdown content
        """
        logger.debug(f"Processing YouTube link message {message.message_id}")

        # Extract URLs from message
        urls = extract_urls(message.text)

        # Get first YouTube URL
        youtube_urls = [url for url in urls if is_youtube_url(url)]

        if not youtube_urls:
            return ProcessedResult(
                markdown_content=f"{message.text}\n\n",
                metadata={"type": "link", "error": "no_youtube_urls"},
            )

        url = youtube_urls[0]
        content_parts = []
        summary = None
        transcript_file = None
        video_file = None

        try:
            # Get video metadata and transcript
            video = await self.youtube_utils.get_video_metadata(url)

            # Format header with title
            content_parts.append(f"**YouTube: {video.title}**\n\n")

            # Add URL
            content_parts.append(f"{url}\n\n")

            # Add metadata
            content_parts.append(f"*Channel: {video.channel}*\n\n")

            # Handle transcript
            transcript_text = None

            if self.config.transcription.youtube_prefer_transcript and video.transcript:
                # Use YouTube's transcript
                transcript_text = video.transcript
                logger.info(f"Using YouTube transcript for {video.video_id}")

                # Save transcript to file
                transcript_filename = generate_youtube_transcript_filename(
                    message.timestamp, video.title
                )
                transcript_file = media_dir / transcript_filename

                with open(transcript_file, "w", encoding="utf-8") as f:
                    f.write(transcript_text)

                logger.info(f"Saved YouTube transcript to {transcript_file}")

            else:
                # No transcript available or preference is to download
                if not video.transcript:
                    logger.info(f"No transcript available for {video.video_id}, downloading video")

                    # Download video
                    video_filename = generate_youtube_transcript_filename(
                        message.timestamp, video.title
                    ).replace("_transcript.txt", "")

                    video_file = await self.youtube_utils.download_video(
                        url, media_dir, video_filename
                    )

                    # Transcribe downloaded video
                    transcript_text = await self.transcriber.transcribe_file(video_file)

                    # Save transcript
                    transcript_filename = generate_youtube_transcript_filename(
                        message.timestamp, video.title
                    )
                    transcript_file = media_dir / transcript_filename

                    with open(transcript_file, "w", encoding="utf-8") as f:
                        f.write(transcript_text)

                    logger.info(f"Transcribed and saved to {transcript_file}")

            # Add transcript link
            if transcript_file:
                content_parts.append(
                    format_transcript_link(
                        transcript_file.name,
                        style=self.config.markdown.wikilink_style,
                    )
                )

            # Generate summary if available
            if transcript_text and self.summarizer and self.config.summarization.enabled:
                try:
                    prompt = self.config.summarization.prompts.youtube_summary
                    summary = await self.summarizer.summarize(
                        transcript_text,
                        prompt=prompt,
                    )

                    if summary:
                        content_parts.append(self._format_summary(summary))

                except Exception as e:
                    logger.warning(f"Failed to generate YouTube summary: {e}")

            markdown_content = "".join(content_parts)

            media_files = []
            if video_file:
                media_files.append(video_file)

            return ProcessedResult(
                markdown_content=markdown_content,
                media_files=media_files,
                transcript_file=transcript_file,
                summary=summary,
                metadata={
                    "type": "youtube",
                    "url": url,
                    "video_id": video.video_id,
                    "title": video.title,
                    "has_transcript": transcript_file is not None,
                    "has_summary": summary is not None,
                    "downloaded_video": video_file is not None,
                },
            )

        except Exception as e:
            logger.error(f"Failed to process YouTube video {url}: {e}")

            # Fallback: just include the link
            content_parts.append(f"**YouTube Video**\n\n")
            content_parts.append(f"{url}\n\n")
            content_parts.append(f"*Failed to process video: {str(e)}*\n\n")

            markdown_content = "".join(content_parts)

            return ProcessedResult(
                markdown_content=markdown_content,
                metadata={"type": "youtube", "url": url, "error": str(e)},
            )
