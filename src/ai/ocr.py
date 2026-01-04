"""OCR (Optical Character Recognition) for extracting text from images.

Supports multiple providers:
- Tesseract: Local OCR using pytesseract
- Cloud providers: Google Vision, Azure, AWS (future)
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

from src.core.config import CloudOCRConfig, OCRConfig, TesseractConfig
from src.core.logger import get_logger

logger = get_logger(__name__)


class OCRProvider(ABC):
    """Abstract base class for OCR providers."""

    @abstractmethod
    async def extract_text(self, image_path: Path) -> str:
        """Extract text from image.

        Args:
            image_path: Path to image file

        Returns:
            Extracted text

        Raises:
            Exception: If OCR fails
        """
        pass


class TesseractOCR(OCRProvider):
    """Local Tesseract OCR provider.

    Uses pytesseract (Python wrapper for Tesseract OCR).
    Requires tesseract binary to be installed on system.
    """

    def __init__(self, config: TesseractConfig):
        """Initialize Tesseract OCR.

        Args:
            config: Tesseract configuration

        Raises:
            ImportError: If pytesseract not installed
            RuntimeError: If tesseract binary not found
        """
        if not TESSERACT_AVAILABLE:
            raise ImportError(
                "pytesseract and Pillow are required for Tesseract OCR. "
                "Install with: pip install pytesseract pillow"
            )

        self.languages = "+".join(config.languages)  # e.g., "eng+fra"
        self.config_str = config.config  # e.g., "--psm 3"

        # Check if tesseract is available
        try:
            pytesseract.get_tesseract_version()
        except Exception as e:
            raise RuntimeError(
                f"Tesseract binary not found. Please install Tesseract OCR. Error: {e}"
            )

        logger.info(f"Initialized Tesseract OCR with languages: {self.languages}")

    async def extract_text(self, image_path: Path) -> str:
        """Extract text from image using Tesseract.

        Args:
            image_path: Path to image file

        Returns:
            Extracted text (empty string if no text found)

        Raises:
            Exception: If image cannot be read or OCR fails
        """
        try:
            # Open image with PIL
            image = Image.open(image_path)

            # Extract text
            # Note: pytesseract.image_to_string is not async, so we run it synchronously
            # For true async, we'd need to use asyncio.to_thread() but that's Python 3.9+
            text = pytesseract.image_to_string(
                image,
                lang=self.languages,
                config=self.config_str,
            )

            # Clean up result
            text = text.strip()

            if text:
                logger.debug(f"Extracted {len(text)} characters from {image_path.name}")
            else:
                logger.debug(f"No text found in {image_path.name}")

            return text

        except Exception as e:
            logger.error(f"Tesseract OCR failed for {image_path}: {e}")
            raise


class CloudOCR(OCRProvider):
    """Cloud OCR provider (Google Vision, Azure, AWS).

    Placeholder implementation for future cloud provider support.
    """

    def __init__(self, config: CloudOCRConfig):
        """Initialize cloud OCR provider.

        Args:
            config: Cloud OCR configuration

        Raises:
            NotImplementedError: Cloud OCR not yet implemented
        """
        self.provider = config.provider
        self.api_key = config.api_key

        # TODO: Initialize provider SDK based on config.provider
        raise NotImplementedError(
            f"Cloud OCR provider '{self.provider}' not yet implemented. "
            "Please use 'tesseract' provider for now."
        )

    async def extract_text(self, image_path: Path) -> str:
        """Extract text from image using cloud provider.

        Args:
            image_path: Path to image file

        Returns:
            Extracted text

        Raises:
            NotImplementedError: Not yet implemented
        """
        # TODO: Implement cloud provider calls
        raise NotImplementedError("Cloud OCR not yet implemented")


class OCRManager:
    """Manages OCR providers and provides unified interface.

    This class handles provider selection, initialization, and error handling.
    """

    def __init__(self, config: OCRConfig):
        """Initialize OCR manager.

        Args:
            config: OCR configuration

        Raises:
            ValueError: If invalid provider specified
            ImportError: If provider dependencies not installed
        """
        self.enabled = config.enabled
        self.provider_name = config.provider

        if not self.enabled:
            logger.info("OCR is disabled in configuration")
            self.provider = None
            return

        # Initialize provider
        try:
            if config.provider == "tesseract":
                self.provider = TesseractOCR(config.tesseract)
            elif config.provider == "cloud":
                self.provider = CloudOCR(config.cloud)
            else:
                raise ValueError(f"Unknown OCR provider: {config.provider}")

            logger.info(f"OCR initialized with provider: {config.provider}")

        except Exception as e:
            logger.error(f"Failed to initialize OCR provider '{config.provider}': {e}")
            logger.warning("OCR will be disabled")
            self.provider = None
            self.enabled = False

    async def extract_text(self, image_path: Path) -> Optional[str]:
        """Extract text from image with error handling.

        Args:
            image_path: Path to image file

        Returns:
            Extracted text, or None if OCR is disabled or fails
        """
        if not self.enabled or not self.provider:
            logger.debug("OCR is disabled, skipping")
            return None

        if not image_path.exists():
            logger.warning(f"Image file not found: {image_path}")
            return None

        try:
            text = await self.provider.extract_text(image_path)
            return text if text else None

        except Exception as e:
            logger.error(f"OCR failed for {image_path}: {e}")
            # Don't raise - OCR failure shouldn't stop processing
            return None

    def is_available(self) -> bool:
        """Check if OCR is available.

        Returns:
            True if OCR is enabled and provider initialized
        """
        return self.enabled and self.provider is not None
