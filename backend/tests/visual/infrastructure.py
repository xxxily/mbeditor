"""Visual parity infrastructure for MBEditor ↔ WeChat draft comparison.

This module provides 5 helper functions used by Task 10/11 visual tests:

    render_mbdoc_to_screenshot  — render MBDoc in headless Chromium → PNG
    push_mbdoc_to_wechat_draft  — push doc to WeChat draft, return media_id
    screenshot_wechat_draft     — screenshot a WeChat draft via logged-in session
    diff_images                 — pixel-level image diff via PIL
    diff_dom                    — structural HTML diff ignoring noisy attrs

Design contract:
  - All 5 functions are pure/independent; each can be called without the others.
  - render_mbdoc_to_screenshot and diff_images/diff_dom do NOT touch WeChat APIs.
  - screenshot_wechat_draft requires a prior auth_login.py run (storage_state).
"""

import difflib
import io
import os
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional

from app.models.mbdoc import MBDoc
from app.services.block_registry import BlockRegistry, RenderContext
from app.services.render_for_wechat import render_for_wechat

# ---------------------------------------------------------------------------
# Default directories
# ---------------------------------------------------------------------------

_THIS_DIR = Path(__file__).parent
_ARTIFACTS_DIR = _THIS_DIR / "_artifacts"
_AUTH_STATE_PATH = _THIS_DIR / ".auth" / "state.json"

# ---------------------------------------------------------------------------
# (a) render_mbdoc_to_screenshot
# ---------------------------------------------------------------------------

_BODY_STYLE = (
    "margin:0;"
    "padding:20px 16px;"
    "font-family:-apple-system,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;"
    "font-size:16px;"
    "line-height:1.8;"
    "color:#333;"
    "background:#fff;"
)


def render_mbdoc_to_screenshot(
    doc: MBDoc,
    out_dir: Optional[Path] = None,
) -> Path:
    """Render an MBDoc to a PNG screenshot via headless Chromium.

    Simulates the MBEditor preview iframe chrome:
      - viewport 375×800px (iPhone SE / mp.weixin mobile preview)
      - body padding/font identical to the iframe wrapper
      - inline styles are the ONLY style source (no CSS reset injected)

    Args:
        doc: source document to render.
        out_dir: directory to write the PNG to. Defaults to
            ``backend/tests/visual/_artifacts/``.

    Returns:
        Path to the written PNG file.
    """
    from playwright.sync_api import sync_playwright

    out_dir = out_dir or _ARTIFACTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    ctx = RenderContext(upload_images=False)
    fragment = render_for_wechat(doc, ctx)

    wrapper_html = (
        "<!DOCTYPE html>"
        "<html>"
        f'<body style="{_BODY_STYLE}">'
        f"{fragment}"
        "</body>"
        "</html>"
    )

    out_path = out_dir / f"{doc.id}_editor.png"

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_viewport_size({"width": 375, "height": 800})
        page.set_content(wrapper_html, wait_until="networkidle")
        page.screenshot(path=str(out_path), full_page=True)
        browser.close()

    return out_path


# ---------------------------------------------------------------------------
# (b) push_mbdoc_to_wechat_draft
# ---------------------------------------------------------------------------


def push_mbdoc_to_wechat_draft(doc: MBDoc) -> str:
    """Push an MBDoc to WeChat as a draft article.

    Renders the document with ``upload_images=True`` (the "push" path) and
    calls ``wechat_service.create_draft``. Requires a valid ``data/config.json``
    with appid/appsecret configured for the MB科技 test account.

    Args:
        doc: document to push.

    Returns:
        The ``media_id`` string returned by the WeChat draft API.
    """
    from app.services import wechat_service

    # Stage 1 has no image blocks; upload_images=True still walks the real
    # push code-path even if no images are actually uploaded.
    ctx = RenderContext(upload_images=True, image_uploader=None)
    html = render_for_wechat(doc, ctx)

    title = doc.meta.title or doc.id
    result = wechat_service.create_draft(title=title, html=html)
    return result["media_id"]


# ---------------------------------------------------------------------------
# (c) screenshot_wechat_draft
# ---------------------------------------------------------------------------


def screenshot_wechat_draft(
    media_id: str,
    out_dir: Optional[Path] = None,
) -> Path:
    """Screenshot a WeChat draft article using a persisted login session.

    Requires a prior successful run of ``auth_login.py`` which saves
    ``backend/tests/visual/.auth/state.json``.

    The WeChat MP draft preview page URL pattern is:
        https://mp.weixin.qq.com/cgi-bin/appmsgpublish?sub=list&type=101

    From the draft list, the function attempts to locate the first draft card
    that links to an article preview and navigate to it.

    TODO (Task 11): Once a user has completed the first auth_login run and
    confirmed the exact draft preview selectors in the WeChat MP backend UI,
    update the selector constants below. The current implementation captures
    the full draft list page as a fallback if the specific draft cannot be
    isolated.

    Args:
        media_id: media_id returned by push_mbdoc_to_wechat_draft.
        out_dir: directory to write the PNG to. Defaults to _artifacts/.

    Returns:
        Path to the written PNG.

    Raises:
        RuntimeError: if .auth/state.json does not exist (not yet logged in)
            or if the WeChat session has expired.
    """
    from playwright.sync_api import sync_playwright

    state_path = _AUTH_STATE_PATH
    if not state_path.exists():
        raise RuntimeError(
            "WeChat login state not found. "
            "Run: python -m backend.tests.visual.auth_login first to scan QR."
        )

    out_dir = out_dir or _ARTIFACTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{media_id}_draft.png"

    # Draft list URL — confirmed entry point for WeChat MP backend draft view
    _DRAFT_LIST_URL = (
        "https://mp.weixin.qq.com/cgi-bin/appmsgpublish?sub=list&type=101"
    )
    # TODO (Task 11): Confirm the exact selector for the draft preview button
    # after the first auth_login run. Options:
    #   - ".weui-desktop-mass-appmsg__meta-title a"  (draft title link)
    #   - "[data-mediaid='<media_id>']"               (if data attr exists)
    # For now we fall back to screenshotting the whole draft list page.
    _DRAFT_PREVIEW_SELECTOR = None  # type: Optional[str]

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            storage_state=str(state_path),
            viewport={"width": 375, "height": 800},
            device_scale_factor=2,
        )
        page = context.new_page()
        page.goto(_DRAFT_LIST_URL, wait_until="networkidle", timeout=30_000)

        # Check if we are still logged in (WeChat MP redirects to login page if not)
        if "mp.weixin.qq.com/cgi-bin" not in page.url:
            browser.close()
            raise RuntimeError(
                f"WeChat session expired or not logged in (landed on {page.url}). "
                "Re-run auth_login."
            )

        if _DRAFT_PREVIEW_SELECTOR:
            # Attempt to navigate to the specific draft preview
            try:
                page.click(_DRAFT_PREVIEW_SELECTOR, timeout=5_000)
                page.wait_for_load_state("networkidle", timeout=15_000)
            except Exception as exc:
                browser.close()
                raise RuntimeError(
                    f"Draft preview selector not found or click timed out: {exc}"
                ) from exc

        # Screenshot whatever page we landed on
        page.screenshot(path=str(out_path), full_page=True)
        browser.close()

    return out_path


# ---------------------------------------------------------------------------
# (d) diff_images
# ---------------------------------------------------------------------------


def diff_images(
    a: Path,
    b: Path,
    tolerance: float = 0.005,
) -> dict:
    """Pixel-level diff between two PNG screenshots.

    Pixels are compared in RGB space; a pixel is considered "different" if
    any channel differs by more than 8 (out of 255).

    Args:
        a: reference image (e.g. editor screenshot).
        b: candidate image (e.g. WeChat draft screenshot). If its size
           differs from ``a``, it is resized to match using LANCZOS.
        tolerance: diff fraction above which a diff image is written. Also
            used by callers to assert visual parity. Default 0.005 (0.5%).

    Returns:
        dict with keys:
            diff_pct       — fraction of differing pixels (0.0–1.0)
            diff_pixels    — absolute count of differing pixels
            total_pixels   — total pixel count (after resize)
            diff_image_path — Path to written diff PNG, or None
    """
    from PIL import Image

    img_a = Image.open(a).convert("RGB")
    img_b = Image.open(b).convert("RGB")

    if img_b.size != img_a.size:
        img_b = img_b.resize(img_a.size, Image.Resampling.LANCZOS)

    width, height = img_a.size
    total = width * height

    # Compare raw bytes: each RGB pixel is 3 bytes; stride = width * 3
    raw_a = img_a.tobytes()
    raw_b = img_b.tobytes()

    diff_count = 0
    diff_mask: list[bool] = []
    stride = 3
    for i in range(total):
        off = i * stride
        is_diff = any(
            abs(int(raw_a[off + c]) - int(raw_b[off + c])) > 8
            for c in range(stride)
        )
        diff_mask.append(is_diff)
        if is_diff:
            diff_count += 1

    diff_pct = diff_count / total if total > 0 else 0.0

    diff_image_path: Optional[Path] = None
    write_diff = (
        diff_pct > tolerance
        or os.environ.get("MBEDITOR_VISUAL_WRITE_DIFF") == "1"
    )
    if write_diff and diff_count > 0:
        diff_pixels_raw = bytearray(total * stride)
        for i, is_diff in enumerate(diff_mask):
            off = i * stride
            if is_diff:
                diff_pixels_raw[off] = 255
                diff_pixels_raw[off + 1] = 0
                diff_pixels_raw[off + 2] = 0
            else:
                diff_pixels_raw[off : off + stride] = raw_a[off : off + stride]
        diff_img = Image.frombytes("RGB", (width, height), bytes(diff_pixels_raw))
        diff_image_path = a.parent / f"{a.stem}_VS_{b.stem}_diff.png"
        diff_img.save(str(diff_image_path))

    return {
        "diff_pct": diff_pct,
        "diff_pixels": diff_count,
        "total_pixels": total,
        "diff_image_path": diff_image_path,
    }


# ---------------------------------------------------------------------------
# (e) diff_dom
# ---------------------------------------------------------------------------


class _NormalizingParser(HTMLParser):
    """HTMLParser that normalises tags/attrs and collapses whitespace."""

    def __init__(self, ignore_attr_prefixes: tuple[str, ...] = ("data-",), ignore_attrs: tuple[str, ...] = ("id",)):
        super().__init__()
        self.ignore_attr_prefixes = ignore_attr_prefixes
        self.ignore_attrs = ignore_attrs
        self.lines: list[str] = []

    def _filter_attrs(self, attrs: list[tuple]) -> list[tuple]:
        result = []
        for name, value in attrs:
            if name in self.ignore_attrs:
                continue
            if any(name.startswith(pfx) for pfx in self.ignore_attr_prefixes):
                continue
            # Strip query string from src
            if name == "src" and value and "?" in value:
                value = value.split("?")[0]
            result.append((name, value))
        return result

    def handle_starttag(self, tag: str, attrs: list[tuple]) -> None:
        filtered = self._filter_attrs(attrs)
        attr_str = ""
        if filtered:
            parts = []
            for name, value in sorted(filtered):
                parts.append(f'{name}="{value}"' if value is not None else name)
            attr_str = " " + " ".join(parts)
        self.lines.append(f"<{tag}{attr_str}>")

    def handle_endtag(self, tag: str) -> None:
        self.lines.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        normalized = re.sub(r"\s+", " ", data).strip()
        if normalized:
            self.lines.append(normalized)


def _normalize_html(html: str, ignore_attr_prefixes: tuple[str, ...], ignore_attrs: tuple[str, ...]) -> list[str]:
    parser = _NormalizingParser(
        ignore_attr_prefixes=ignore_attr_prefixes,
        ignore_attrs=ignore_attrs,
    )
    parser.feed(html)
    return parser.lines


def diff_dom(
    html_a: str,
    html_b: str,
    ignore_attrs: tuple[str, ...] = ("data-", "id"),
) -> dict:
    """Structural HTML diff, ignoring noisy runtime attributes.

    Strips attributes whose names start with ``data-`` or equal ``id``,
    removes query strings from ``src`` values, and collapses whitespace
    before comparing. Uses ``difflib.unified_diff`` for the diff text.

    Args:
        html_a: reference HTML string.
        html_b: candidate HTML string.
        ignore_attrs: attribute names / prefixes to strip before comparison.
            Entries ending with ``-`` are treated as prefixes.

    Returns:
        dict with keys:
            equal — True if the normalised representations are identical
            diff  — unified diff text (empty string when equal)
    """
    # Split ignore_attrs into prefixes (end with "-") and exact names
    prefixes = tuple(a for a in ignore_attrs if a.endswith("-"))
    exact = tuple(a for a in ignore_attrs if not a.endswith("-"))

    lines_a = _normalize_html(html_a, ignore_attr_prefixes=prefixes, ignore_attrs=exact)
    lines_b = _normalize_html(html_b, ignore_attr_prefixes=prefixes, ignore_attrs=exact)

    if lines_a == lines_b:
        return {"equal": True, "diff": ""}

    diff_lines = list(
        difflib.unified_diff(
            lines_a,
            lines_b,
            fromfile="html_a",
            tofile="html_b",
            lineterm="",
        )
    )
    return {"equal": False, "diff": "\n".join(diff_lines)}
