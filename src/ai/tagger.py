"""Auto-tagging for messages.

Supports multiple tagging methods:
- Rule-based: Regex patterns for deterministic tagging
- AI-based: LLM-powered tag generation (optional)
"""

import re
from typing import List, Optional, Set

from src.core.config import AITaggingConfig, TaggingConfig, TaggingRule
from src.core.logger import get_logger
from src.processors.base import ProcessedResult
from src.telegram.fetcher import Message

logger = get_logger(__name__)


class RuleBasedTagger:
    """Apply tags based on regex pattern rules.

    This tagger matches content against predefined patterns and applies
    corresponding tags. It's fast, deterministic, and requires no external APIs.
    """

    def __init__(self, rules: List[TaggingRule]):
        """Initialize rule-based tagger.

        Args:
            rules: List of tagging rules with patterns and tags
        """
        self.rules = rules
        logger.info(f"Initialized rule-based tagger with {len(rules)} rules")

    def generate_tags(
        self,
        message: Message,
        result: ProcessedResult,
    ) -> List[str]:
        """Generate tags based on pattern rules.

        Args:
            message: Message to tag
            result: Processing result with additional content

        Returns:
            List of tags (e.g., ["#screenshot", "#image"])
        """
        tags: Set[str] = set()

        # Get all text content to match against
        content_parts = []
        if message.text:
            content_parts.append(message.text)
        if message.caption:
            content_parts.append(message.caption)
        if result.ocr_text:
            content_parts.append(result.ocr_text)
        if result.summary:
            content_parts.append(result.summary)

        combined_content = " ".join(content_parts).lower()

        # Match against rules
        for rule in self.rules:
            try:
                if re.search(rule.pattern, combined_content, re.IGNORECASE):
                    tags.add(rule.tag)
            except re.error as e:
                logger.warning(f"Invalid regex pattern '{rule.pattern}': {e}")

        # Type-based tags (always applied)
        type_tags = self._get_type_tags(message, result)
        tags.update(type_tags)

        # Feature-based tags
        if result.transcript_file:
            tags.add("#transcription")
        if result.ocr_text:
            tags.add("#ocr")
        if result.summary:
            tags.add("#summarized")

        return sorted(list(tags))

    def _get_type_tags(self, message: Message, result: ProcessedResult) -> Set[str]:
        """Get tags based on message type.

        Args:
            message: Message object
            result: Processing result

        Returns:
            Set of type-based tags
        """
        tags = set()

        # Media type tags
        message_type = result.message_type or message.message_type
        type_map = {
            "image": "#image",
            "photo": "#image",
            "video": "#video",
            "audio": "#audio",
            "voice": "#voice",
            "document": "#document",
            "link": "#link",
        }

        if message_type in type_map:
            tags.add(type_map[message_type])

        # YouTube special case
        if message_type == "link" and message.text:
            if "youtube.com" in message.text or "youtu.be" in message.text:
                tags.add("#youtube")

        return tags


class AITagger:
    """AI-based tagging using LLM.

    This tagger uses a language model to generate contextual tags.
    It's more flexible but slower and requires an AI provider.
    """

    def __init__(self, config: AITaggingConfig):
        """Initialize AI tagger.

        Args:
            config: AI tagging configuration

        Raises:
            NotImplementedError: AI tagging not yet implemented
        """
        self.enabled = config.enabled
        self.provider = config.provider
        self.model = config.model
        self.max_tags = config.max_tags
        self.prompt = config.prompt

        if self.enabled:
            # TODO: Initialize AI provider (Ollama, etc.)
            logger.warning("AI-based tagging is not yet fully implemented")
            # For now, disable it
            self.enabled = False

    async def generate_tags(self, content: str) -> List[str]:
        """Generate tags using LLM.

        Args:
            content: Content to analyze

        Returns:
            List of AI-generated tags

        Raises:
            NotImplementedError: Not yet implemented
        """
        if not self.enabled:
            return []

        # TODO: Implement AI tagging
        # 1. Call LLM with content and prompt
        # 2. Parse response to extract tags
        # 3. Validate and format tags
        # 4. Return up to max_tags

        logger.debug("AI tagging called but not implemented, returning empty list")
        return []


class Tagger:
    """Main tagging interface.

    Combines multiple tagging methods (rules + AI) to generate comprehensive tags.
    """

    def __init__(self, config: TaggingConfig):
        """Initialize tagger.

        Args:
            config: Tagging configuration
        """
        self.enabled = config.enabled
        self.rule_tagger = RuleBasedTagger(config.rules) if config.enabled else None
        self.ai_tagger = (
            AITagger(config.ai_tagging) if config.enabled and config.ai_tagging.enabled else None
        )

        if not self.enabled:
            logger.info("Tagging is disabled in configuration")
        else:
            logger.info(
                f"Tagging initialized (rules: {bool(self.rule_tagger)}, "
                f"AI: {bool(self.ai_tagger and self.ai_tagger.enabled)})"
            )

    async def generate_tags(
        self,
        message: Message,
        result: ProcessedResult,
    ) -> List[str]:
        """Generate tags using all enabled methods.

        Args:
            message: Message to tag
            result: Processing result

        Returns:
            Combined list of unique tags from all methods
        """
        if not self.enabled:
            return []

        tags: Set[str] = set()

        # Rule-based tagging (always enabled if tagging is enabled)
        if self.rule_tagger:
            rule_tags = self.rule_tagger.generate_tags(message, result)
            tags.update(rule_tags)
            logger.debug(f"Rule-based tagger generated {len(rule_tags)} tags")

        # AI-based tagging (optional)
        if self.ai_tagger and self.ai_tagger.enabled:
            # Prepare content for AI
            content_parts = []
            if message.text:
                content_parts.append(message.text)
            if message.caption:
                content_parts.append(message.caption)
            if result.ocr_text:
                content_parts.append(result.ocr_text[:500])  # Limit OCR text

            content = " ".join(content_parts)

            if content:
                ai_tags = await self.ai_tagger.generate_tags(content)
                tags.update(ai_tags)
                logger.debug(f"AI tagger generated {len(ai_tags)} tags")

        # Sort and return
        sorted_tags = sorted(list(tags))
        logger.debug(f"Total tags generated: {len(sorted_tags)}")
        return sorted_tags

    def is_available(self) -> bool:
        """Check if tagging is available.

        Returns:
            True if tagging is enabled
        """
        return self.enabled and self.rule_tagger is not None
