"""Tests for checksum utilities."""

from pathlib import Path

import pytest

from src.utils.checksum import calculate_checksum, compare_checksums, has_file_changed


def test_calculate_checksum(temp_dir):
    """Test checksum calculation."""
    # Create a test file
    test_file = temp_dir / "test.txt"
    test_file.write_text("Hello, World!")

    # Calculate checksum
    checksum = calculate_checksum(test_file)

    # Should be a 64-character hex string (SHA-256)
    assert isinstance(checksum, str)
    assert len(checksum) == 64
    assert all(c in "0123456789abcdef" for c in checksum)


def test_calculate_checksum_consistency(temp_dir):
    """Test that checksum is consistent for same content."""
    # Create two files with identical content
    file1 = temp_dir / "file1.txt"
    file2 = temp_dir / "file2.txt"

    content = "Identical content for testing"
    file1.write_text(content)
    file2.write_text(content)

    # Checksums should be identical
    checksum1 = calculate_checksum(file1)
    checksum2 = calculate_checksum(file2)

    assert checksum1 == checksum2


def test_calculate_checksum_different_content(temp_dir):
    """Test that different content produces different checksums."""
    file1 = temp_dir / "file1.txt"
    file2 = temp_dir / "file2.txt"

    file1.write_text("Content A")
    file2.write_text("Content B")

    checksum1 = calculate_checksum(file1)
    checksum2 = calculate_checksum(file2)

    assert checksum1 != checksum2


def test_calculate_checksum_nonexistent_file(temp_dir):
    """Test checksum calculation for nonexistent file."""
    nonexistent = temp_dir / "nonexistent.txt"

    with pytest.raises(FileNotFoundError):
        calculate_checksum(nonexistent)


def test_compare_checksums_match(temp_dir):
    """Test comparing checksums that match."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("Test content")

    checksum = calculate_checksum(test_file)

    assert compare_checksums(test_file, checksum) is True


def test_compare_checksums_mismatch(temp_dir):
    """Test comparing checksums that don't match."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("Test content")

    # Use a fake checksum
    fake_checksum = "0" * 64

    assert compare_checksums(test_file, fake_checksum) is False


def test_has_file_changed_unchanged(temp_dir):
    """Test detecting unchanged file."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("Original content")

    # Get original checksum
    original_checksum = calculate_checksum(test_file)

    # File hasn't changed
    assert has_file_changed(test_file, original_checksum) is False


def test_has_file_changed_modified(temp_dir):
    """Test detecting modified file."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("Original content")

    # Get original checksum
    original_checksum = calculate_checksum(test_file)

    # Modify file
    test_file.write_text("Modified content")

    # File has changed
    assert has_file_changed(test_file, original_checksum) is True


def test_has_file_changed_empty_file(temp_dir):
    """Test checksum of empty file."""
    empty_file = temp_dir / "empty.txt"
    empty_file.write_text("")

    checksum = calculate_checksum(empty_file)

    # Should still produce valid checksum
    assert isinstance(checksum, str)
    assert len(checksum) == 64


def test_has_file_changed_large_file(temp_dir):
    """Test checksum of larger file."""
    large_file = temp_dir / "large.txt"

    # Create a file with 1MB of data
    content = "x" * (1024 * 1024)
    large_file.write_text(content)

    checksum = calculate_checksum(large_file)

    # Should handle large files
    assert isinstance(checksum, str)
    assert len(checksum) == 64
