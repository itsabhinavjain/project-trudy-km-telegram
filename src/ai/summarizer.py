"""Base summarizer interface."""

from abc import ABC, abstractmethod
from typing import Optional


class Summarizer(ABC):
    """Abstract base class for content summarization."""

    @abstractmethod
    async def summarize(
        self,
        content: str,
        prompt: Optional[str] = None,
    ) -> str:
        """Generate a summary of the content.

        Args:
            content: Content to summarize
            prompt: Optional custom prompt (overrides default)

        Returns:
            Summary text

        Raises:
            Exception: If summarization fails
        """
        pass

    def _truncate_content(self, content: str, max_length: int = 10000) -> str:
        """Truncate content to maximum length.

        Args:
            content: Content to truncate
            max_length: Maximum length in characters

        Returns:
            Truncated content
        """
        if len(content) <= max_length:
            return content

        # Truncate and add indicator
        return content[:max_length] + "\n\n[Content truncated...]"
