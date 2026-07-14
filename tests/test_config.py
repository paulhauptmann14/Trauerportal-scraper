import os
import stat

import pytest

from pnp_watcher.config import Config, check_env_permissions


def clear_pnp_env(monkeypatch):
    for key in [
        "TARGET_CITY",
        "EDITION_ID",
        "LOOKBACK_DAYS",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "STATE_PATH",
    ]:
        monkeypatch.delenv(key, raising=False)


def test_load_raises_when_target_city_missing(monkeypatch, tmp_path):
    clear_pnp_env(monkeypatch)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError):
        Config.load()


def test_load_raises_when_target_city_is_placeholder(monkeypatch, tmp_path):
    clear_pnp_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TARGET_CITY", "YOUR_TOWN")

    with pytest.raises(ValueError):
        Config.load()


def test_load_applies_defaults(monkeypatch, tmp_path):
    clear_pnp_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TARGET_CITY", "Fiktingen")

    config = Config.load()

    assert config.target_city == "Fiktingen"
    assert config.edition_id == 8
    assert config.lookback_days == 14
    assert config.telegram_bot_token == ""
    assert config.telegram_chat_id == ""


def test_load_reads_overrides(monkeypatch, tmp_path):
    clear_pnp_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TARGET_CITY", "Fiktingen")
    monkeypatch.setenv("LOOKBACK_DAYS", "3")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")

    config = Config.load()

    assert config.lookback_days == 3
    assert config.telegram_bot_token == "123:ABC"
    assert config.telegram_chat_id == "42"


def test_check_env_permissions_flags_group_readable_file(tmp_path):
    path = tmp_path / ".env"
    path.write_text("TELEGRAM_BOT_TOKEN=secret\n")
    os.chmod(path, 0o644)

    warning = check_env_permissions(str(path))

    assert warning is not None
    assert str(path) in warning


def test_check_env_permissions_accepts_owner_only_file(tmp_path):
    path = tmp_path / ".env"
    path.write_text("TELEGRAM_BOT_TOKEN=secret\n")
    os.chmod(path, 0o600)

    warning = check_env_permissions(str(path))

    assert warning is None


def test_check_env_permissions_ignores_missing_file():
    assert check_env_permissions("") is None
    assert check_env_permissions("/nonexistent/.env") is None
