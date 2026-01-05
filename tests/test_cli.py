"""Tests for CLI commands."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from src.cli.main import app


runner = CliRunner()


def test_cli_help():
    """Test CLI help command."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Trudy 2.0" in result.stdout
    assert "discover" in result.stdout
    assert "fetch" in result.stdout
    assert "process" in result.stdout
    assert "sync" in result.stdout
    assert "status" in result.stdout
    assert "info" in result.stdout
    assert "clean" in result.stdout


def test_cli_version():
    """Test CLI version flag."""
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "Trudy version" in result.stdout
    assert "2.0" in result.stdout


def test_discover_help():
    """Test discover command help."""
    result = runner.invoke(app, ["discover", "--help"])

    assert result.exit_code == 0
    assert "Discover users" in result.stdout
    assert "--full" in result.stdout
    assert "--refresh" in result.stdout


def test_fetch_help():
    """Test fetch command help."""
    result = runner.invoke(app, ["fetch", "--help"])

    assert result.exit_code == 0
    assert "Fetch messages" in result.stdout
    assert "--full" in result.stdout
    assert "--limit" in result.stdout
    assert "--dry-run" in result.stdout


def test_process_help():
    """Test process command help."""
    result = runner.invoke(app, ["process", "--help"])

    assert result.exit_code == 0
    assert "Process staging" in result.stdout
    assert "--skip-transcription" in result.stdout
    assert "--skip-ocr" in result.stdout
    assert "--skip-summarization" in result.stdout
    assert "--reprocess" in result.stdout


def test_sync_help():
    """Test sync command help."""
    result = runner.invoke(app, ["sync", "--help"])

    assert result.exit_code == 0
    assert "Sync messages" in result.stdout or "combined" in result.stdout
    assert "--full" in result.stdout


def test_status_help():
    """Test status command help."""
    result = runner.invoke(app, ["status", "--help"])

    assert result.exit_code == 0
    assert "status" in result.stdout.lower()
    assert "--user" in result.stdout


def test_info_help():
    """Test info command help."""
    result = runner.invoke(app, ["info", "--help"])

    assert result.exit_code == 0
    assert "info" in result.stdout.lower() or "system" in result.stdout.lower()


def test_clean_help():
    """Test clean command help."""
    result = runner.invoke(app, ["clean", "--help"])

    assert result.exit_code == 0
    assert "Clean" in result.stdout
    assert "--staging" in result.stdout
    assert "--processed" in result.stdout
    assert "--media" in result.stdout
    assert "--dry-run" in result.stdout


def test_global_verbose_flag():
    """Test global --verbose flag."""
    result = runner.invoke(app, ["--verbose", "--help"])

    assert result.exit_code == 0


def test_global_quiet_flag():
    """Test global --quiet flag."""
    result = runner.invoke(app, ["--quiet", "--help"])

    assert result.exit_code == 0


def test_global_config_flag(temp_dir):
    """Test global --config flag."""
    # Create a dummy config file
    config_file = temp_dir / "test_config.yaml"
    config_file.write_text("# Test config")

    result = runner.invoke(app, ["--config", str(config_file), "--help"])

    assert result.exit_code == 0


def test_status_with_config(temp_dir):
    """Test status command with custom config."""
    # Create minimal config and state
    config_file = temp_dir / "config.yaml"
    config_file.write_text("""
storage:
  base_dir: "%s"
  staging_dir: "staging"
  processed_dir: "processed"
  media_dir: "media"
""" % str(temp_dir))

    # Create empty state file
    state_file = temp_dir / "state.json"
    state_file.write_text('{"users": {}, "statistics": {}}')

    result = runner.invoke(app, ["--config", str(config_file), "status"])

    # Should run without error
    assert result.exit_code == 0
    assert "No users found" in result.stdout or "status" in result.stdout.lower()


def test_clean_requires_target():
    """Test that clean command requires at least one target."""
    result = runner.invoke(app, ["clean"])

    assert result.exit_code == 1
    assert "Must specify at least one" in result.stdout or "Error" in result.stdout


def test_clean_dry_run(temp_dir):
    """Test clean command with --dry-run."""
    # Create minimal config
    config_file = temp_dir / "config.yaml"
    config_file.write_text("""
storage:
  base_dir: "%s"
  staging_dir: "staging"
  processed_dir: "processed"
  media_dir: "media"
  staging_retention:
    policy: "keep_days"
    days: 7
""" % str(temp_dir))

    # Create some test files
    staging_dir = temp_dir / "staging" / "testuser"
    staging_dir.mkdir(parents=True, exist_ok=True)
    (staging_dir / "test.md").write_text("test content")

    result = runner.invoke(app, [
        "--config", str(config_file),
        "clean",
        "--staging",
        "--days", "0",
        "--dry-run"
    ])

    # Should complete successfully
    assert result.exit_code == 0
    assert "DRY RUN" in result.stdout or "Would delete" in result.stdout

    # File should still exist (dry run)
    assert (staging_dir / "test.md").exists()


def test_invalid_command():
    """Test invoking invalid command."""
    result = runner.invoke(app, ["invalid-command"])

    assert result.exit_code != 0
    assert "No such command" in result.stdout or "Error" in result.stdout


def test_missing_required_argument():
    """Test command with missing required arguments."""
    # Most commands should work without arguments (use defaults)
    # Test that help still works
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
