"""Link/article processor for handling article URLs."""

from pathlib import Path
from typing import Optional

from src.core.logger import get_logger
from src.markdown.formatter import extract_urls, is_youtube_url
from src.processors.base import BaseProcessor, ProcessedResult
from src.telegram.fetcher import Message
from src.utils.article_extractor import ArticleExtractor

logger = get_logger(__name__)


class LinkProcessor(BaseProcessor):
    """Processes article links (non-YouTube URLs)."""

    def __init__(
        self,
        config,
        article_extractor: ArticleExtractor,
        summarizer: Optional[object] = None,
    ):
        """Initialize link processor.

        Args:
            config: Application configuration
            article_extractor: Article extractor instance
            summarizer: Optional summarizer instance
        """
        super().__init__(config)
        self.article_extractor = article_extractor
        self.summarizer = summarizer

    async def can_process(self, message: Message) -> bool:
        """Check if this is a link message (but not YouTube).

        Args:
            message: Message to check

        Returns:
            True if message contains article link
        """
        if message.message_type != "link" or not message.text:
            return False

        # Extract URLs
        urls = extract_urls(message.text)
        if not urls:
            return False

        # Check if any URL is NOT a YouTube link
        return any(not is_youtube_url(url) for url in urls)

    async def process(
        self,
        message: Message,
        media_dir: Path,
        notes_dir: Path,
    ) -> ProcessedResult:
        """Process an article link.

        Args:
            message: Message to process
            media_dir: Directory for media files (unused)
            notes_dir: Directory for notes

        Returns:
            Processed result with markdown content
        """
        logger.debug(f"Processing article link message {message.message_id}")

        # Extract URLs from message
        urls = extract_urls(message.text)

        # Filter out YouTube URLs
        article_urls = [url for url in urls if not is_youtube_url(url)]

        if not article_urls:
            return ProcessedResult(
                markdown_content=f"{message.text}\n\n",
                message_type="link",
                reply_to=message.reply_to,
                forwarded_from=message.forwarded_from,
                edited_at=message.edited_at,
                metadata={"error": "no_article_urls"},
            )

        # Process first article URL
        url = article_urls[0]

        content_parts = []
        summary = None

        try:
            # Extract article
            article = await self.article_extractor.extract(url)

            # Format header with title
            title = article.title or "Article"
            content_parts.append(f"**Article: {title}**\n\n")

            # Add URL
            content_parts.append(f"{url}\n\n")

            # Add metadata if available
            if article.author or article.publish_date:
                metadata_parts = []
                if article.author:
                    metadata_parts.append(f"Author: {article.author}")
                if article.publish_date:
                    metadata_parts.append(f"Published: {article.publish_date}")
                content_parts.append(f"*{' | '.join(metadata_parts)}*\n\n")

            # Generate summary if summarizer is available
            if self.summarizer and self.config.summarization.enabled:
                try:
                    prompt = self.config.summarization.prompts.article_summary
                    summary = await self.summarizer.summarize(
                        article.text,
                        prompt=prompt,
                    )

                    if summary:
                        content_parts.append(self._format_summary(summary))

                except Exception as e:
                    logger.warning(f"Failed to generate article summary: {e}")

            markdown_content = "".join(content_parts)

            # Build link metadata for v2.0
            link_metadata = {
                "url": url,
                "title": article.title or "Unknown",
            }
            if article.description:
                link_metadata["description"] = article.description

            return ProcessedResult(
                markdown_content=markdown_content,
                message_type="link",
                summary=summary,
                links=[link_metadata],  # v2.0: Structured link metadata
                reply_to=message.reply_to,  # v2.0: Preserve context
                forwarded_from=message.forwarded_from,  # v2.0: Preserve context
                edited_at=message.edited_at,  # v2.0: Preserve context
                metadata={
                    "url": url,
                    "title": article.title,
                    "has_summary": summary is not None,
                },
            )

        except Exception as e:
            logger.error(f"Failed to process article {url}: {e}")

            # Fallback: just include the link
            content_parts.append(f"**Article Link**\n\n")
            content_parts.append(f"{url}\n\n")
            content_parts.append(f"*Failed to extract article: {str(e)}*\n\n")

            markdown_content = "".join(content_parts)

            return ProcessedResult(
                markdown_content=markdown_content,
                message_type="link",
                reply_to=message.reply_to,
                forwarded_from=message.forwarded_from,
                edited_at=message.edited_at,
                metadata={"url": url, "error": str(e)},
            )
