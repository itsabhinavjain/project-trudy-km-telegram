"""Article extraction from URLs using Trafilatura and Newspaper3k."""

from dataclasses import dataclass
from typing import Optional

import trafilatura
from newspaper import Article

from src.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ExtractedArticle:
    """Extracted article content."""

    title: Optional[str]
    author: Optional[str]
    publish_date: Optional[str]
    text: str
    url: str


class ArticleExtractor:
    """Extracts article content from URLs."""

    async def extract(self, url: str) -> ExtractedArticle:
        """Extract article content from URL.

        Args:
            url: URL to extract from

        Returns:
            Extracted article

        Raises:
            Exception: If extraction fails
        """
        logger.info(f"Extracting article from: {url}")

        # Try Trafilatura first (faster and better for most sites)
        try:
            return await self._extract_with_trafilatura(url)
        except Exception as e:
            logger.warning(f"Trafilatura extraction failed: {e}, trying Newspaper3k")

        # Fallback to Newspaper3k
        try:
            return await self._extract_with_newspaper(url)
        except Exception as e:
            logger.error(f"All extraction methods failed for {url}: {e}")
            raise Exception(f"Failed to extract article: {e}") from e

    async def _extract_with_trafilatura(self, url: str) -> ExtractedArticle:
        """Extract article using Trafilatura.

        Args:
            url: URL to extract from

        Returns:
            Extracted article

        Raises:
            Exception: If extraction fails
        """
        # Download and extract
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            raise Exception("Failed to fetch URL")

        # Extract text content
        text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=True,
            include_links=False,
        )

        if not text:
            raise Exception("Failed to extract text content")

        # Extract metadata
        metadata = trafilatura.extract_metadata(downloaded)

        title = None
        author = None
        publish_date = None

        if metadata:
            title = metadata.title
            author = metadata.author
            publish_date = metadata.date

        return ExtractedArticle(
            title=title,
            author=author,
            publish_date=publish_date,
            text=text,
            url=url,
        )

    async def _extract_with_newspaper(self, url: str) -> ExtractedArticle:
        """Extract article using Newspaper3k.

        Args:
            url: URL to extract from

        Returns:
            Extracted article

        Raises:
            Exception: If extraction fails
        """
        article = Article(url)
        article.download()
        article.parse()

        if not article.text:
            raise Exception("Failed to extract article text")

        return ExtractedArticle(
            title=article.title or None,
            author=", ".join(article.authors) if article.authors else None,
            publish_date=str(article.publish_date) if article.publish_date else None,
            text=article.text,
            url=url,
        )
