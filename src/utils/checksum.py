"""File checksum utilities for detecting changes in staging files."""

import hashlib
from pathlib import Path
from typing import Optional


def calculate_checksum(filepath: Path) -> str:
    """Calculate SHA-256 checksum of a file.

    Args:
        filepath: Path to file

    Returns:
        Hex digest of SHA-256 checksum

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file can't be read
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    sha256 = hashlib.sha256()

    # Read file in chunks to handle large files efficiently
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)

    return sha256.hexdigest()


def compare_checksums(filepath: Path, expected_checksum: str) -> bool:
    """Check if file matches expected checksum.

    Args:
        filepath: Path to file
        expected_checksum: Expected SHA-256 checksum (hex digest)

    Returns:
        True if checksums match, False otherwise
    """
    try:
        actual_checksum = calculate_checksum(filepath)
        return actual_checksum == expected_checksum
    except (FileNotFoundError, IOError):
        return False


def has_file_changed(filepath: Path, stored_checksum: Optional[str]) -> bool:
    """Check if file has changed since last checksum was stored.

    Args:
        filepath: Path to file
        stored_checksum: Previously stored checksum (None if never checksummed)

    Returns:
        True if file has changed (or no stored checksum), False if unchanged
    """
    # If no stored checksum, consider it changed
    if stored_checksum is None:
        return True

    # If file doesn't exist, consider it changed
    if not filepath.exists():
        return True

    # Compare checksums
    try:
        current_checksum = calculate_checksum(filepath)
        return current_checksum != stored_checksum
    except (FileNotFoundError, IOError):
        return True


def calculate_checksums_for_directory(
    directory: Path,
    pattern: str = "*.md"
) -> dict[str, str]:
    """Calculate checksums for all files matching pattern in directory.

    Args:
        directory: Directory to scan
        pattern: Glob pattern for files (default: "*.md")

    Returns:
        Dictionary mapping file paths (as strings) to checksums
    """
    checksums = {}

    if not directory.exists():
        return checksums

    for filepath in directory.glob(pattern):
        if filepath.is_file():
            try:
                checksum = calculate_checksum(filepath)
                checksums[str(filepath)] = checksum
            except (FileNotFoundError, IOError):
                # Skip files that can't be read
                continue

    return checksums
