"""Ollama-based summarization."""

from typing import Optional

import ollama

from src.ai.summarizer import Summarizer
from src.core.config import SummarizationConfig
from src.core.logger import get_logger

logger = get_logger(__name__)


class OllamaSummarizer(Summarizer):
    """Summarizes content using Ollama local models."""

    def __init__(self, config: SummarizationConfig):
        """Initialize Ollama summarizer.

        Args:
            config: Summarization configuration
        """
        self.config = config
        self.client = ollama.Client(host=config.ollama.base_url)

    async def summarize(
        self,
        content: str,
        prompt: Optional[str] = None,
    ) -> str:
        """Generate a summary using Ollama.

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
        content = self._truncate_content(content, max_length=15000)

        # Build full prompt
        if not prompt:
            prompt = "Summarize the following content in a clear and concise manner:"

        full_prompt = f"{prompt}\n\n{content}"

        logger.info(f"Generating summary using Ollama ({self.config.ollama.model})")

        try:
            response = self.client.generate(
                model=self.config.ollama.model,
                prompt=full_prompt,
                options={
                    "temperature": self.config.ollama.temperature,
                    "num_predict": self.config.ollama.max_tokens,
                },
            )

            summary = response["response"].strip()

            logger.info("Summary generated successfully")
            return summary

        except Exception as e:
            logger.error(f"Ollama summarization failed: {e}")
            raise Exception(f"Summarization failed: {e}") from e
