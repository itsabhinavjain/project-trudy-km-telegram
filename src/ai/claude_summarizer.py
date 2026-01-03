"""Claude Code CLI-based summarization."""

import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from src.ai.summarizer import Summarizer
from src.core.config import SummarizationConfig
from src.core.logger import get_logger

logger = get_logger(__name__)


class ClaudeSummarizer(Summarizer):
    """Summarizes content using Claude Code CLI."""

    def __init__(self, config: SummarizationConfig):
        """Initialize Claude summarizer.

        Args:
            config: Summarization configuration
        """
        self.config = config

    async def summarize(
        self,
        content: str,
        prompt: Optional[str] = None,
    ) -> str:
        """Generate a summary using Claude Code CLI.

        Args:
            content: Content to summarize
            prompt: Optional custom prompt template

        Returns:
            Summary text

        Raises:
            Exception: If summarization fails
        """
        if not self.config.enabled:
            logger.warning("Summarization is disabled")
            return "[Summarization disabled]"

        # Truncate content if too long
        content = self._truncate_content(content, max_length=20000)

        # Build full prompt
        if not prompt:
            prompt = "Summarize the following content in a clear and concise manner:"

        full_prompt = f"{prompt}\n\n{content}"

        logger.info("Generating summary using Claude Code CLI")

        try:
            # Write content to temporary file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False, encoding="utf-8"
            ) as temp_file:
                temp_file.write(full_prompt)
                temp_path = Path(temp_file.name)

            try:
                # Call Claude Code CLI
                result = subprocess.run(
                    [
                        self.config.claude.cli_path,
                        "chat",
                        "--message",
                        f"@{temp_path}",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120,  # 2 minutes
                )

                if result.returncode != 0:
                    raise Exception(f"Claude CLI failed: {result.stderr}")

                summary = result.stdout.strip()

                logger.info("Summary generated successfully with Claude")
                return summary

            finally:
                # Clean up temporary file
                if temp_path.exists():
                    temp_path.unlink()

        except FileNotFoundError:
            logger.error(
                f"Claude Code CLI not found at: {self.config.claude.cli_path}"
            )
            raise Exception(
                "Claude Code CLI not found. Make sure it's installed and in PATH."
            )
        except subprocess.TimeoutExpired:
            raise Exception("Claude CLI summarization timed out")
        except Exception as e:
            logger.error(f"Claude summarization failed: {e}")
            raise Exception(f"Summarization failed: {e}") from e
