import pytest

from pnp_watcher.config import Config, parse_notification_channels


def clear_pnp_env(monkeypatch):
    for key in [
        "TARGET_CITY",
        "EDITION_ID",
        "LOOKBACK_DAYS",
        "NOTIFICATION_CHANNEL",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_USER",
        "SMTP_PASSWORD",
        "NOTIFY_EMAIL_TO",
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
    assert config.notification_channels == ("telegram",)
    assert config.telegram_bot_token == ""
    assert config.telegram_chat_id == ""
    assert config.smtp_host == "smtp.mail.me.com"
    assert config.smtp_port == 587
    assert config.smtp_user == ""
    assert config.smtp_password == ""
    assert config.notify_email_to == ""


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


def test_load_normalizes_notification_channel_case(monkeypatch, tmp_path):
    clear_pnp_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TARGET_CITY", "Fiktingen")
    monkeypatch.setenv("NOTIFICATION_CHANNEL", "Email")

    config = Config.load()

    assert config.notification_channels == ("email",)


def test_load_parses_multiple_notification_channels(monkeypatch, tmp_path):
    clear_pnp_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TARGET_CITY", "Fiktingen")
    monkeypatch.setenv("NOTIFICATION_CHANNEL", "telegram, Email")

    config = Config.load()

    assert config.notification_channels == ("telegram", "email")


def test_load_reads_email_overrides(monkeypatch, tmp_path):
    clear_pnp_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TARGET_CITY", "Fiktingen")
    monkeypatch.setenv("NOTIFICATION_CHANNEL", "email")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USER", "me@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret")
    monkeypatch.setenv("NOTIFY_EMAIL_TO", "me@example.com")

    config = Config.load()

    assert config.smtp_host == "smtp.example.com"
    assert config.smtp_port == 465
    assert config.smtp_user == "me@example.com"
    assert config.smtp_password == "secret"
    assert config.notify_email_to == "me@example.com"


def test_load_raises_on_invalid_notification_channel(monkeypatch, tmp_path):
    clear_pnp_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TARGET_CITY", "Fiktingen")
    monkeypatch.setenv("NOTIFICATION_CHANNEL", "sms")

    with pytest.raises(ValueError):
        Config.load()


def test_parse_notification_channels_single():
    assert parse_notification_channels("telegram") == ("telegram",)


def test_parse_notification_channels_multiple_comma_separated():
    assert parse_notification_channels("telegram,email") == ("telegram", "email")


def test_parse_notification_channels_strips_whitespace_and_lowercases():
    assert parse_notification_channels(" Telegram , Email ") == ("telegram", "email")


def test_parse_notification_channels_dedupes_preserving_order():
    assert parse_notification_channels("telegram,email,telegram") == ("telegram", "email")


def test_parse_notification_channels_raises_on_unknown_channel():
    with pytest.raises(ValueError):
        parse_notification_channels("telegram,sms")


def test_parse_notification_channels_raises_on_empty_string():
    with pytest.raises(ValueError):
        parse_notification_channels("")
