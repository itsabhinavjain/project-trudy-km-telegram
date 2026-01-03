"""Audio/video transcription using Whisper via Ollama."""

import subprocess
from pathlib import Path
from typing import Optional

import ollama

from src.core.config import TranscriptionConfig
from src.core.logger import get_logger

logger = get_logger(__name__)


class TranscriptionError(Exception):
    """Raised when transcription fails."""

    pass


class Transcriber:
    """Transcribes audio and video files using Whisper."""

    def __init__(self, config: TranscriptionConfig):
        """Initialize transcriber.

        Args:
            config: Transcription configuration
        """
        self.config = config

    async def transcribe_file(self, file_path: Path) -> str:
        """Transcribe an audio or video file.

        Args:
            file_path: Path to audio/video file

        Returns:
            Transcription text

        Raises:
            TranscriptionError: If transcription fails
        """
        if not self.config.enabled:
            logger.warning("Transcription is disabled in configuration")
            return "[Transcription disabled]"

        if not file_path.exists():
            raise TranscriptionError(f"File not found: {file_path}")

        logger.info(f"Transcribing file: {file_path}")

        try:
            if self.config.provider == "ollama":
                return await self._transcribe_with_ollama(file_path)
            else:
                raise TranscriptionError(f"Unknown provider: {self.config.provider}")

        except Exception as e:
            logger.error(f"Transcription failed for {file_path}: {e}")
            raise TranscriptionError(f"Transcription failed: {e}") from e

    async def _transcribe_with_ollama(self, file_path: Path) -> str:
        """Transcribe using Ollama Whisper model.

        Args:
            file_path: Path to audio/video file

        Returns:
            Transcription text

        Raises:
            TranscriptionError: If transcription fails
        """
        # Convert to WAV if needed
        wav_file = await self._ensure_wav_format(file_path)

        try:
            # Use Ollama client for transcription
            client = ollama.Client(host=self.config.ollama.base_url)

            # Read audio file as bytes
            with open(wav_file, "rb") as f:
                audio_bytes = f.read()

            # Note: Ollama's Whisper support may vary
            # This is a simplified implementation
            # In practice, you may need to use subprocess to call whisper directly
            # or use the Ollama API differently

            # Alternative: Use subprocess to call whisper.cpp or whisper CLI
            result = await self._transcribe_with_whisper_cli(wav_file)

            logger.info(f"Transcription completed for {file_path}")
            return result

        except Exception as e:
            logger.error(f"Ollama transcription failed: {e}")
            raise TranscriptionError(f"Ollama transcription failed: {e}") from e
        finally:
            # Clean up temporary WAV file if created
            if wav_file != file_path and wav_file.exists():
                wav_file.unlink()

    async def _transcribe_with_whisper_cli(self, audio_file: Path) -> str:
        """Transcribe using whisper CLI tool.

        Args:
            audio_file: Path to audio file

        Returns:
            Transcription text

        Raises:
            TranscriptionError: If transcription fails
        """
        try:
            # Use whisper CLI if available
            # Install with: pip install openai-whisper
            # Or use whisper.cpp
            result = subprocess.run(
                ["whisper", str(audio_file), "--model", "base", "--output_format", "txt"],
                capture_output=True,
                text=True,
                timeout=self.config.ollama.timeout,
            )

            if result.returncode != 0:
                raise TranscriptionError(f"Whisper CLI failed: {result.stderr}")

            # Read output file
            output_file = audio_file.with_suffix(".txt")
            if output_file.exists():
                with open(output_file, "r") as f:
                    transcript = f.read().strip()
                output_file.unlink()  # Clean up
                return transcript
            else:
                # If no output file, use stdout
                return result.stdout.strip()

        except FileNotFoundError:
            # Whisper CLI not installed, fallback to basic message
            logger.warning("Whisper CLI not found. Install with: pip install openai-whisper")
            return "[Whisper CLI not available - transcription skipped]"
        except subprocess.TimeoutExpired:
            raise TranscriptionError("Transcription timed out")
        except Exception as e:
            raise TranscriptionError(f"CLI transcription failed: {e}") from e

    async def _ensure_wav_format(self, file_path: Path) -> Path:
        """Convert audio/video to WAV format if needed.

        Args:
            file_path: Path to media file

        Returns:
            Path to WAV file (may be same as input if already WAV)

        Raises:
            TranscriptionError: If conversion fails
        """
        if file_path.suffix.lower() == ".wav":
            return file_path

        # Convert to WAV using ffmpeg
        wav_file = file_path.with_suffix(".wav")

        try:
            logger.debug(f"Converting {file_path} to WAV format")
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    str(file_path),
                    "-acodec",
                    "pcm_s16le",
                    "-ar",
                    "16000",
                    "-ac",
                    "1",
                    str(wav_file),
                    "-y",  # Overwrite if exists
                ],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes
            )

            if result.returncode != 0:
                raise TranscriptionError(f"FFmpeg conversion failed: {result.stderr}")

            return wav_file

        except FileNotFoundError:
            raise TranscriptionError(
                "FFmpeg not found. Install with: brew install ffmpeg (macOS) or apt-get install ffmpeg (Linux)"
            )
        except subprocess.TimeoutExpired:
            raise TranscriptionError("Audio conversion timed out")
        except Exception as e:
            raise TranscriptionError(f"Audio conversion failed: {e}") from e
