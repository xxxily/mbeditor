"""Tests for WeChat API proxy configuration.

Uses behavior-level assertions via httpx.Client mocking instead of
checking private internals like _transport._pool._proxy.
"""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from app.services import wechat_service
from app.api.v1 import wechat


@pytest.fixture
def temp_config(tmp_path: Path):
    """Provide a temporary config file for testing."""
    config_file = tmp_path / "config.json"
    config_file.write_text('{"appid": "wx123", "appsecret": "secret456"}')
    original = wechat_service.settings.CONFIG_FILE
    wechat_service.settings.CONFIG_FILE = str(config_file)
    wechat_service._token_cache.clear()
    wechat_service._proxy_client_cache.clear()
    wechat_service._direct_client = None
    yield config_file
    wechat_service.settings.CONFIG_FILE = original


class TestGetHttpClient:
    """Tests for the HTTP client factory with proxy support."""

    def test_no_proxy_config_sends_none_to_httpx(self, temp_config):
        """When proxy_url is absent, get_http_client passes proxy=None to httpx."""
        with patch("app.services.wechat_service.httpx.Client") as MockClient:
            MockClient.return_value = MagicMock()
            wechat_service._proxy_client_cache.clear()

            wechat_service.get_http_client()

            MockClient.assert_called_once()
            kwargs = MockClient.call_args[1]
            assert kwargs.get("proxy") is None

    def test_proxy_config_passed_to_httpx(self, temp_config):
        """When proxy_url is set, it is forwarded to httpx.Client."""
        config = json.loads(temp_config.read_text())
        config["proxy_url"] = "https://proxy.example.com:8080"
        temp_config.write_text(json.dumps(config))
        wechat_service._proxy_client_cache.clear()

        with patch("app.services.wechat_service.httpx.Client") as MockClient:
            MockClient.return_value = MagicMock()
            wechat_service.get_http_client()

            kwargs = MockClient.call_args[1]
            assert kwargs.get("proxy") == "https://proxy.example.com:8080"

    def test_same_proxy_returns_cached_client(self, temp_config):
        """Same proxy URL returns the same cached client instance."""
        config = json.loads(temp_config.read_text())
        config["proxy_url"] = "https://proxy.example.com:8080"
        temp_config.write_text(json.dumps(config))
        wechat_service._proxy_client_cache.clear()

        client1 = wechat_service.get_http_client()
        client2 = wechat_service.get_http_client()
        assert client1 is client2


class TestGetDirectClient:
    """Tests for the direct (non-proxied) HTTP client used for remote image fetching."""

    def test_direct_client_sends_none_to_httpx(self, temp_config):
        """get_direct_client must NOT use proxy even when proxy_url is configured."""
        config = json.loads(temp_config.read_text())
        config["proxy_url"] = "https://proxy.example.com:8080"
        temp_config.write_text(json.dumps(config))
        wechat_service._direct_client = None

        with patch("app.services.wechat_service.httpx.Client") as MockClient:
            MockClient.return_value = MagicMock()
            wechat_service.get_direct_client()

            kwargs = MockClient.call_args[1]
            assert kwargs.get("proxy") is None

    def test_direct_client_is_singleton(self, temp_config):
        """get_direct_client returns the same instance on repeated calls."""
        wechat_service._direct_client = None

        client1 = wechat_service.get_direct_client()
        client2 = wechat_service.get_direct_client()
        assert client1 is client2

    def test_direct_client_independent_of_proxy_config(self, temp_config):
        """get_http_client uses proxy while get_direct_client ignores it."""
        config = json.loads(temp_config.read_text())
        config["proxy_url"] = "https://proxy.evil.com:9999"
        temp_config.write_text(json.dumps(config))
        wechat_service._proxy_client_cache.clear()
        wechat_service._direct_client = None

        with patch("app.services.wechat_service.httpx.Client") as MockClient:
            MockClient.return_value = MagicMock()

            wechat_service.get_http_client()
            http_call = MockClient.call_args
            wechat_service.get_direct_client()
            direct_call = MockClient.call_args

            assert http_call[1].get("proxy") == "https://proxy.evil.com:9999"
            assert direct_call[1].get("proxy") is None


class TestProxyConfigSaveLoad:
    """Tests for proxy_url persistence in config.json."""

    def test_save_config_includes_proxy_url(self, temp_config):
        """save_config writes proxy_url to config.json."""
        wechat_service.save_config(
            "wx123", "secret456", "https://proxy.example.com:8080"
        )
        config = json.loads(temp_config.read_text())
        assert config["proxy_url"] == "https://proxy.example.com:8080"

    def test_save_config_empty_proxy(self, temp_config):
        """save_config with empty proxy_url still writes the field."""
        wechat_service.save_config("wx123", "secret456", "")
        config = json.loads(temp_config.read_text())
        assert config["proxy_url"] == ""

    def test_load_config_returns_proxy_url(self, temp_config):
        """load_config includes proxy_url when present."""
        config_data = {
            "appid": "wx123",
            "appsecret": "sec",
            "proxy_url": "http://proxy:8080",
        }
        temp_config.write_text(json.dumps(config_data))
        result = wechat_service.load_config()
        assert result["proxy_url"] == "http://proxy:8080"

    def test_load_config_missing_proxy_url(self, temp_config):
        """load_config handles old config without proxy_url (backward compat)."""
        temp_config.write_text('{"appid": "wx123", "appsecret": "sec"}')
        result = wechat_service.load_config()
        assert result.get("proxy_url") is None


class TestProxyUrlValidation:
    """Tests for proxy URL format validation."""

    def test_valid_http_proxy(self):
        assert wechat_service._validate_proxy_url("http://proxy:8080") is True

    def test_valid_https_proxy(self):
        assert wechat_service._validate_proxy_url("https://proxy:8080") is True

    def test_valid_socks5_proxy(self):
        assert wechat_service._validate_proxy_url("socks5://proxy:1080") is True

    def test_invalid_no_protocol(self):
        assert wechat_service._validate_proxy_url("proxy:8080") is False

    def test_invalid_empty(self):
        assert wechat_service._validate_proxy_url("") is False


class TestProxyUrlMasking:
    """Tests for credential masking in GET /config response."""

    def test_no_credentials_unchanged(self):
        assert (
            wechat._mask_proxy_credentials("https://proxy.example.com:8080")
            == "https://proxy.example.com:8080"
        )

    def test_credentials_masked(self):
        result = wechat._mask_proxy_credentials(
            "http://user:pass@proxy.example.com:8080"
        )
        assert "user" not in result
        assert "pass" not in result
        assert "****:****@" in result
        assert "proxy.example.com:8080" in result

    def test_empty_unchanged(self):
        assert wechat._mask_proxy_credentials("") == ""

    def test_invalid_url_passthrough(self):
        assert wechat._mask_proxy_credentials("not-a-url") == "not-a-url"
