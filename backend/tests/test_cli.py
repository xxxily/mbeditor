"""Tests for the MBEditor CLI (app.cli.main).

Covers:
  - Direct-mode article / doc / image / render / skill / info commands
  - HTTP-mode smoke via mocked httpx.Client.request
  - Output envelope shape, --json / --compact / --quiet
  - Exit codes: 0 success, 1 executor error, 2 validation error
"""
from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from app.cli.main import app


runner = CliRunner()


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    (tmp_path / "articles").mkdir()
    (tmp_path / "mbdocs").mkdir()
    (tmp_path / "images").mkdir()
    return tmp_path


@pytest.fixture(autouse=True)
def _reset_app_settings():
    """Snapshot & restore core settings mutated by --data-dir override."""
    from app.core import config as config_mod

    snapshot = {
        key: getattr(config_mod.settings, key)
        for key in ("ARTICLES_DIR", "MBDOCS_DIR", "IMAGES_DIR", "CONFIG_FILE")
    }
    yield
    for key, value in snapshot.items():
        setattr(config_mod.settings, key, value)


def _parse(result) -> dict:
    payload = json.loads(result.stdout)
    assert isinstance(payload, dict)
    return payload


def _invoke(data_dir: Path, *args: str, extra: list[str] | None = None):
    base = ["--data-dir", str(data_dir)]
    if extra:
        base = extra + base
    return runner.invoke(app, base + list(args))


def _tiny_png() -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (2, 2), color=(255, 128, 0)).save(buf, format="PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# info / skill / version
# ---------------------------------------------------------------------------


def test_info_reports_direct_mode_and_data_paths(data_dir):
    result = _invoke(data_dir, "info")
    assert result.exit_code == 0, result.stdout
    payload = _parse(result)
    assert payload["ok"] is True
    assert payload["action"] == "info"
    assert payload["data"]["mode"] == "direct"
    assert payload["data"]["version"] == "4.0.0"
    for key in ("articles", "mbdocs", "images", "config"):
        assert str(data_dir) in payload["data"]["paths"][key]


def test_info_version_subcommand(data_dir):
    result = _invoke(data_dir, "info", "version")
    assert result.exit_code == 0
    assert _parse(result)["data"] == {"version": "4.0.0"}


def test_info_paths_subcommand(data_dir):
    result = _invoke(data_dir, "info", "paths")
    assert result.exit_code == 0
    payload = _parse(result)
    for key in ("articles", "mbdocs", "images", "config"):
        assert key in payload["data"]


def test_skill_default_prints_markdown(data_dir):
    result = _invoke(data_dir, "skill")
    assert result.exit_code == 0
    assert "MBEditor CLI Skill" in result.stdout
    assert "Output Contract" in result.stdout


def test_skill_json_wraps_markdown_in_envelope(data_dir):
    result = _invoke(data_dir, "--json", "skill")
    assert result.exit_code == 0
    payload = _parse(result)
    assert payload["action"] == "skill.show"
    assert "MBEditor CLI Skill" in payload["data"]["skill"]


def test_skill_path_returns_real_file(data_dir):
    result = _invoke(data_dir, "skill", "path")
    assert result.exit_code == 0
    payload = _parse(result)
    assert Path(payload["data"]["path"]).name == "SKILL.md"


# ---------------------------------------------------------------------------
# article CRUD (direct)
# ---------------------------------------------------------------------------


def test_article_create_then_list_get(data_dir):
    create = _invoke(data_dir, "article", "create", "My Title", "markdown")
    assert create.exit_code == 0, create.stdout
    article = _parse(create)["data"]
    assert article["title"] == "My Title"
    assert article["mode"] == "markdown"
    aid = article["id"]

    listing = _invoke(data_dir, "article", "list")
    assert listing.exit_code == 0
    rows = _parse(listing)["data"]
    assert any(row["id"] == aid for row in rows)

    get = _invoke(data_dir, "article", "get", aid)
    assert get.exit_code == 0
    got = _parse(get)["data"]
    assert got["id"] == aid and got["title"] == "My Title"


def test_article_create_defaults_mode_html(data_dir):
    result = _invoke(data_dir, "article", "create", "Defaulted")
    assert result.exit_code == 0
    assert _parse(result)["data"]["mode"] == "html"


def test_article_update_without_flags_exits_with_validation_code(data_dir):
    created = _invoke(data_dir, "article", "create", "T")
    aid = _parse(created)["data"]["id"]

    bad = _invoke(data_dir, "article", "update", aid)
    assert bad.exit_code == 2
    payload = _parse(bad)
    assert payload["ok"] is False
    assert "no update" in payload["message"].lower()


def test_article_update_applies_markdown_and_preserves_other_fields(data_dir):
    created = _invoke(data_dir, "article", "create", "Orig", "markdown")
    aid = _parse(created)["data"]["id"]

    upd = _invoke(data_dir, "article", "update", aid, "--markdown", "# Hello")
    assert upd.exit_code == 0
    data = _parse(upd)["data"]
    assert data["markdown"] == "# Hello"
    assert data["title"] == "Orig"


def test_article_delete_then_get_returns_not_found(data_dir):
    created = _invoke(data_dir, "article", "create", "Gone")
    aid = _parse(created)["data"]["id"]

    dele = _invoke(data_dir, "article", "delete", aid)
    assert dele.exit_code == 0
    assert _parse(dele)["data"]["id"] == aid

    missing = _invoke(data_dir, "article", "get", aid)
    assert missing.exit_code == 1
    payload = _parse(missing)
    assert payload["ok"] is False
    assert "not found" in payload["message"].lower()


def test_article_project_to_doc_returns_projection_and_persists(data_dir):
    created = _invoke(data_dir, "article", "create", "Project Me", "markdown")
    aid = _parse(created)["data"]["id"]

    _invoke(data_dir, "article", "update", aid, "--markdown", "# Hi")

    project = _invoke(data_dir, "article", "project-to-doc", aid, "--persist")
    assert project.exit_code == 0
    doc_payload = _parse(project)["data"]
    assert doc_payload["id"] == aid
    assert "projection" in doc_payload
    assert doc_payload["projection"]["editability"] in {"reversible", "informational-only"}

    stored = _invoke(data_dir, "doc", "get", aid)
    assert stored.exit_code == 0, stored.stdout


# ---------------------------------------------------------------------------
# doc CRUD + render (direct)
# ---------------------------------------------------------------------------


def _write_doc_file(path: Path, doc_id: str = "d_hello") -> Path:
    payload = {
        "id": doc_id,
        "version": "1",
        "meta": {"title": "Hi"},
        "blocks": [
            {"type": "heading", "id": "h1", "level": 1, "text": "Hello"},
            {"type": "paragraph", "id": "p1", "text": "World"},
        ],
    }
    file = path / f"{doc_id}.json"
    file.write_text(json.dumps(payload), encoding="utf-8")
    return file


def test_doc_create_rejects_invalid_payload(data_dir, tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"id": "x", "version": "1", "blocks": [{"type": "unknown"}]}), encoding="utf-8")

    result = _invoke(data_dir, "doc", "create", str(bad))
    assert result.exit_code == 1
    payload = _parse(result)
    assert payload["ok"] is False
    assert "invalid" in payload["message"].lower()


def test_doc_create_then_get_and_list(data_dir, tmp_path):
    doc_file = _write_doc_file(tmp_path, "d_roundtrip")

    created = _invoke(data_dir, "doc", "create", str(doc_file))
    assert created.exit_code == 0, created.stdout

    listing = _invoke(data_dir, "doc", "list")
    assert "d_roundtrip" in _parse(listing)["data"]

    got = _invoke(data_dir, "doc", "get", "d_roundtrip")
    assert got.exit_code == 0
    assert _parse(got)["data"]["meta"]["title"] == "Hi"


def test_doc_update_rejects_id_mismatch(data_dir, tmp_path):
    doc_file = _write_doc_file(tmp_path, "d_alpha")
    _invoke(data_dir, "doc", "create", str(doc_file))

    beta_file = _write_doc_file(tmp_path, "d_beta")
    result = _invoke(data_dir, "doc", "update", "d_alpha", str(beta_file))
    assert result.exit_code == 1
    payload = _parse(result)
    assert "does not match" in payload["message"]


def test_doc_render_preview_returns_html(data_dir, tmp_path):
    doc_file = _write_doc_file(tmp_path, "d_render")
    _invoke(data_dir, "doc", "create", str(doc_file))

    rendered = _invoke(data_dir, "doc", "render", "d_render")
    assert rendered.exit_code == 0
    data = _parse(rendered)["data"]
    assert "<h1" in data["html"]
    assert "Hello" in data["html"]
    assert data["upload_images"] is False


def test_doc_render_upload_images_text_only_goes_through(data_dir, tmp_path, monkeypatch):
    doc_file = _write_doc_file(tmp_path, "d_upload")
    _invoke(data_dir, "doc", "create", str(doc_file))

    calls = {"count": 0}

    def _fake_uploader(image_bytes: bytes, filename: str) -> str:
        calls["count"] += 1
        return f"https://cdn.example/{filename}"

    monkeypatch.setattr("app.services.wechat_service.upload_image_to_wechat", _fake_uploader)

    rendered = _invoke(data_dir, "doc", "render", "d_upload", "--upload-images")
    assert rendered.exit_code == 0
    assert _parse(rendered)["data"]["upload_images"] is True
    assert calls["count"] == 0  # text-only doc: uploader should not be invoked


def test_doc_render_raster_without_uploader_fails_at_publish(data_dir, tmp_path, monkeypatch):
    from app.services.renderers import raster_renderer

    monkeypatch.setattr(raster_renderer, "render_raster_png", lambda block: b"FAKEPNG")

    raster_doc = {
        "id": "d_raster",
        "version": "1",
        "meta": {"title": "R"},
        "blocks": [
            {"type": "raster", "id": "r1", "html": "<div>x</div>", "css": "", "width": 320},
        ],
    }
    file = tmp_path / "raster.json"
    file.write_text(json.dumps(raster_doc), encoding="utf-8")

    _invoke(data_dir, "doc", "create", str(file))

    result = _invoke(data_dir, "doc", "render", "d_raster", "--upload-images")
    assert result.exit_code == 1
    payload = _parse(result)
    assert payload["ok"] is False
    msg = payload["message"].lower()
    # Either the WeChat creds are missing (uploader fails immediately) or the
    # raster renderer's own uploader-required guard fires. Both are acceptable
    # end states: the invariant is that raster never emits a data: URL into
    # a publish-mode render.
    assert any(token in msg for token in ("image_uploader", "appsecret", "not configured"))


def test_doc_delete_then_get_returns_not_found(data_dir, tmp_path):
    doc_file = _write_doc_file(tmp_path, "d_gone")
    _invoke(data_dir, "doc", "create", str(doc_file))

    dele = _invoke(data_dir, "doc", "delete", "d_gone")
    assert dele.exit_code == 0

    missing = _invoke(data_dir, "doc", "get", "d_gone")
    assert missing.exit_code == 1
    assert _parse(missing)["ok"] is False


# ---------------------------------------------------------------------------
# image (direct)
# ---------------------------------------------------------------------------


def test_image_upload_list_delete_roundtrip(data_dir, tmp_path):
    png_path = tmp_path / "fixture.png"
    png_path.write_bytes(_tiny_png())

    upload = _invoke(data_dir, "image", "upload", str(png_path))
    assert upload.exit_code == 0, upload.stdout
    record = _parse(upload)["data"]
    image_id = record["id"]

    listing = _invoke(data_dir, "image", "list")
    assert any(item["id"] == image_id for item in _parse(listing)["data"])

    dele = _invoke(data_dir, "image", "delete", image_id)
    assert dele.exit_code == 0

    listing2 = _invoke(data_dir, "image", "list")
    assert all(item["id"] != image_id for item in _parse(listing2)["data"])


def test_image_upload_missing_file_is_validation_error(data_dir, tmp_path):
    result = _invoke(data_dir, "image", "upload", str(tmp_path / "does-not-exist.png"))
    assert result.exit_code == 2
    payload = _parse(result)
    assert payload["ok"] is False
    assert "not found" in payload["message"].lower()


# ---------------------------------------------------------------------------
# render preview (direct)
# ---------------------------------------------------------------------------


def test_render_preview_wraps_html_in_section(data_dir):
    result = _invoke(data_dir, "render", "preview", "<h1>Hi</h1>")
    assert result.exit_code == 0
    assert "<h1>Hi</h1>" in _parse(result)["data"]["html"]


# ---------------------------------------------------------------------------
# output flags
# ---------------------------------------------------------------------------


def test_compact_json_is_single_line(data_dir):
    result = _invoke(data_dir, "info", extra=["--json", "--compact"])
    assert result.exit_code == 0
    out = result.stdout.strip()
    assert "\n" not in out
    json.loads(out)


def test_quiet_suppresses_success_output_but_not_errors(data_dir):
    ok = _invoke(data_dir, "info", extra=["--quiet"])
    assert ok.exit_code == 0
    assert ok.stdout.strip() == ""

    err = _invoke(data_dir, "article", "get", "nope", extra=["--quiet"])
    assert err.exit_code == 1
    assert err.stdout.strip() != ""


# ---------------------------------------------------------------------------
# http-mode smoke (mocked httpx)
# ---------------------------------------------------------------------------


class _FakeResponse:
    def __init__(self, payload: Any, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            import httpx

            raise httpx.HTTPStatusError("boom", request=None, response=self)  # type: ignore[arg-type]


class _FakeClient:
    def __init__(self, script: list[tuple[tuple, dict, _FakeResponse]]):
        self.script = list(script)
        self.calls: list[tuple[str, str, dict]] = []

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        if not self.script:
            raise AssertionError(f"unexpected {method} {url}")
        expected_args, _, response = self.script.pop(0)
        exp_method, exp_url = expected_args
        assert method == exp_method, (method, exp_method)
        assert url.endswith(exp_url), (url, exp_url)
        return response


def _patched_httpx(script):
    fake = _FakeClient(script)

    def _factory(*args, **kwargs):
        return fake

    return fake, patch("app.cli.executor.httpx.Client", _factory)


def test_http_mode_article_list_hits_get_articles():
    fake, patched = _patched_httpx(
        [(("GET", "/articles"), {}, _FakeResponse({"code": 0, "data": [{"id": "a"}]}))]
    )
    with patched:
        result = runner.invoke(app, ["--mode", "http", "article", "list"])
    assert result.exit_code == 0
    assert _parse(result)["data"] == [{"id": "a"}]
    assert fake.calls[0][0] == "GET"


def test_http_mode_doc_create_posts_json(tmp_path):
    doc_file = _write_doc_file(tmp_path, "d_http")
    fake, patched = _patched_httpx(
        [(("POST", "/mbdoc"), {}, _FakeResponse({"code": 0, "data": {"id": "d_http"}}))]
    )
    with patched:
        result = runner.invoke(app, ["--mode", "http", "doc", "create", str(doc_file)])
    assert result.exit_code == 0
    assert _parse(result)["data"] == {"id": "d_http"}
    method, url, kwargs = fake.calls[0]
    assert method == "POST" and url.endswith("/mbdoc")
    assert kwargs["json"]["id"] == "d_http"


def test_http_mode_publish_draft_posts_body():
    fake, patched = _patched_httpx(
        [
            (
                ("POST", "/publish/draft"),
                {},
                _FakeResponse({"code": 0, "data": {"media_id": "m1"}}),
            )
        ]
    )
    with patched:
        result = runner.invoke(
            app, ["--mode", "http", "publish", "draft", "a1", "Author", "Digest"]
        )
    assert result.exit_code == 0
    assert _parse(result)["data"] == {"media_id": "m1"}
    assert fake.calls[0][2]["json"] == {
        "article_id": "a1",
        "author": "Author",
        "digest": "Digest",
    }


def test_http_mode_surface_500_as_executor_error():
    fake, patched = _patched_httpx(
        [(("GET", "/articles"), {}, _FakeResponse({}, status_code=500))]
    )
    with patched:
        result = runner.invoke(app, ["--mode", "http", "article", "list"])
    assert result.exit_code == 1
    payload = _parse(result)
    assert payload["ok"] is False


def test_http_mode_non_zero_envelope_is_executor_error():
    fake, patched = _patched_httpx(
        [
            (
                ("GET", "/articles/xx"),
                {},
                _FakeResponse({"code": 404, "message": "not found", "data": None}),
            )
        ]
    )
    with patched:
        result = runner.invoke(app, ["--mode", "http", "article", "get", "xx"])
    assert result.exit_code == 1
    payload = _parse(result)
    assert payload["ok"] is False
    assert "not found" in payload["message"].lower()


# ---------------------------------------------------------------------------
# mode validation
# ---------------------------------------------------------------------------


def test_invalid_mode_is_usage_error(data_dir):
    result = runner.invoke(app, ["--mode", "bogus", "--data-dir", str(data_dir), "info"])
    assert result.exit_code == 2
    combined = (result.stdout or "") + (result.stderr or "")
    assert "direct" in combined and "http" in combined


# ---------------------------------------------------------------------------
# exit-code matrix (redundant sanity)
# ---------------------------------------------------------------------------


def test_exit_code_success_is_zero(data_dir):
    assert _invoke(data_dir, "info").exit_code == 0


def test_exit_code_validation_is_two(data_dir):
    created = _invoke(data_dir, "article", "create", "X")
    aid = _parse(created)["data"]["id"]
    assert _invoke(data_dir, "article", "update", aid).exit_code == 2


def test_exit_code_executor_error_is_one(data_dir):
    assert _invoke(data_dir, "article", "get", "nonexistent").exit_code == 1
