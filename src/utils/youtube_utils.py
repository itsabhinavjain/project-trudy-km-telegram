"""YouTube utilities for transcript fetching and metadata extraction."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pytube import YouTube
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

from src.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class YouTubeVideo:
    """YouTube video metadata and transcript."""

    video_id: str
    url: str
    title: str
    channel: str
    duration: int  # seconds
    transcript: Optional[str] = None
    video_file: Optional[Path] = None


class YouTubeUtils:
    """Utilities for working with YouTube videos."""

    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """Extract video ID from YouTube URL.

        Args:
            url: YouTube URL

        Returns:
            Video ID or None if not found
        """
        patterns = [
            r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    async def get_transcript(self, video_id: str) -> Optional[str]:
        """Get transcript for a YouTube video.

        Args:
            video_id: YouTube video ID

        Returns:
            Transcript text or None if unavailable
        """
        try:
            # Try to get English transcript first
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])

            # Combine transcript segments
            transcript_text = " ".join([segment["text"] for segment in transcript_list])

            logger.info(f"Retrieved transcript for video {video_id}")
            return transcript_text

        except (TranscriptsDisabled, NoTranscriptFound) as e:
            logger.warning(f"Transcript not available for {video_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to fetch transcript for {video_id}: {e}")
            return None

    async def get_video_metadata(self, url: str) -> YouTubeVideo:
        """Get metadata for a YouTube video.

        Args:
            url: YouTube URL

        Returns:
            YouTubeVideo with metadata

        Raises:
            Exception: If metadata extraction fails
        """
        video_id = self.extract_video_id(url)
        if not video_id:
            raise ValueError(f"Invalid YouTube URL: {url}")

        try:
            yt = YouTube(url)

            # Get transcript if available
            transcript = await self.get_transcript(video_id)

            return YouTubeVideo(
                video_id=video_id,
                url=url,
                title=yt.title,
                channel=yt.author,
                duration=yt.length,
                transcript=transcript,
            )

        except Exception as e:
            logger.error(f"Failed to get metadata for {url}: {e}")
            raise Exception(f"Failed to get YouTube metadata: {e}") from e

    async def download_video(
        self,
        url: str,
        output_dir: Path,
        filename: str,
    ) -> Path:
        """Download YouTube video.

        Args:
            url: YouTube URL
            output_dir: Directory to save video
            filename: Desired filename (without extension)

        Returns:
            Path to downloaded video

        Raises:
            Exception: If download fails
        """
        try:
            yt = YouTube(url)

            # Get highest resolution stream
            stream = yt.streams.get_highest_resolution()

            logger.info(f"Downloading YouTube video: {yt.title}")

            # Download video
            output_file = stream.download(
                output_path=str(output_dir),
                filename=filename,
            )

            logger.info(f"Downloaded to: {output_file}")
            return Path(output_file)

        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            raise Exception(f"YouTube download failed: {e}") from e
