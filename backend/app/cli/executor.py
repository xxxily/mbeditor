"""Executor abstraction for the MBEditor CLI.

Two backends implement the same interface:

- ``DirectExecutor``: calls local services (article_service, MBDocStorage,
  image_service, render_for_wechat) straight from the CLI process. No HTTP
  server needed. This is the default mode so agents can do article and
  document work without spinning up FastAPI.

- ``HttpExecutor``: posts to the running ``/api/v1`` backend. Required for
  WeChat-touching operations (``publish draft``, ``config check``) since
  those share credential/token caches with the server.

All methods return plain Python data (dict/list/str). The CLI command
modules wrap that data in the ``ok/action/message/data`` envelope via
``formatters.emit_success``.

Errors bubble out as ``ExecutorError``; the CLI layer converts them into
``ok=false`` payloads with a non-zero exit code.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Protocol

import httpx

from app.cli.state import CLISettings


class ExecutorError(RuntimeError):
    """Raised when any executor operation fails."""

    def __init__(self, message: str, *, status_code: int | None = None, payload: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class NotSupportedInMode(ExecutorError):
    """Raised when an operation is not available in the current executor mode."""


class Executor(Protocol):
    mode: str

    # --- article ---
    def article_list(self) -> list[dict]: ...
    def article_get(self, article_id: str) -> dict: ...
    def article_create(self, title: str, mode: str) -> dict: ...
    def article_update(self, article_id: str, updates: dict) -> dict: ...
    def article_delete(self, article_id: str) -> None: ...

    # --- doc (MBDoc) ---
    def doc_list(self) -> list[str]: ...
    def doc_get(self, doc_id: str) -> dict: ...
    def doc_create(self, doc_json: dict) -> dict: ...
    def doc_update(self, doc_id: str, doc_json: dict) -> dict: ...
    def doc_delete(self, doc_id: str) -> None: ...
    def doc_render(self, doc_id: str, upload_images: bool) -> dict: ...

    # --- image ---
    def image_list(self) -> list[dict]: ...
    def image_upload(self, file_path: Path) -> dict: ...
    def image_delete(self, image_id: str) -> None: ...

    # --- render ---
    def render_preview(self, html: str, css: str) -> dict: ...
    def render_article(self, article_id: str) -> dict: ...

    # --- publish ---
    def publish_process(self, article_id: str, author: str, digest: str) -> dict: ...
    def publish_draft(self, article_id: str, author: str, digest: str) -> dict: ...

    # --- config ---
    def config_get(self) -> dict: ...
    def config_set(self, appid: str, appsecret: str) -> dict: ...
    def config_check(self, appid: str, appsecret: str) -> dict: ...

    # --- projection ---
    def article_project_to_doc(self, article_id: str, persist: bool) -> dict: ...


# ---------------------------------------------------------------------------
# DirectExecutor
# ---------------------------------------------------------------------------


@dataclass
class DirectExecutor:
    """Executes CLI operations by calling local services directly.

    Requires backend Python deps to be importable (they are, when running
    from within the backend package). Does NOT require the FastAPI server
    to be running.
    """

    settings: CLISettings
    mode: str = "direct"

    # article --------------------------------------------------------------

    def article_list(self) -> list[dict]:
        from app.services import article_service

        return article_service.list_articles()

    def article_get(self, article_id: str) -> dict:
        from app.core.exceptions import AppError
        from app.services import article_service

        try:
            return article_service.get_article(article_id)
        except AppError as exc:
            raise ExecutorError(exc.message, status_code=exc.code) from exc

    def article_create(self, title: str, mode: str) -> dict:
        from app.services import article_service

        return article_service.create_article(title, mode)

    def article_update(self, article_id: str, updates: dict) -> dict:
        from app.core.exceptions import AppError
        from app.services import article_service

        try:
            return article_service.update_article(article_id, updates)
        except AppError as exc:
            raise ExecutorError(exc.message, status_code=exc.code) from exc

    def article_delete(self, article_id: str) -> None:
        from app.core.exceptions import AppError
        from app.services import article_service

        try:
            article_service.delete_article(article_id)
        except AppError as exc:
            raise ExecutorError(exc.message, status_code=exc.code) from exc

    # doc -----------------------------------------------------------------

    def _storage(self):
        from app.services.mbdoc_storage import MBDocStorage

        return MBDocStorage()

    def doc_list(self) -> list[str]:
        return self._storage().list_ids()

    def doc_get(self, doc_id: str) -> dict:
        from app.services.mbdoc_storage import MBDocNotFoundError

        try:
            return self._storage().get(doc_id).model_dump(mode="json")
        except MBDocNotFoundError as exc:
            raise ExecutorError(str(exc), status_code=404) from exc

    def doc_create(self, doc_json: dict) -> dict:
        from app.models.mbdoc import MBDoc

        try:
            doc = MBDoc.model_validate(doc_json)
        except Exception as exc:
            raise ExecutorError(f"invalid MBDoc payload: {exc}", status_code=422) from exc
        self._storage().save(doc)
        return doc.model_dump(mode="json")

    def doc_update(self, doc_id: str, doc_json: dict) -> dict:
        if doc_json.get("id") not in (None, doc_id):
            raise ExecutorError(
                f"document id in payload ({doc_json.get('id')!r}) does not match URL id ({doc_id!r})",
                status_code=400,
            )
        doc_json["id"] = doc_id
        return self.doc_create(doc_json)

    def doc_delete(self, doc_id: str) -> None:
        from app.services.mbdoc_storage import MBDocNotFoundError

        try:
            self._storage().delete(doc_id)
        except MBDocNotFoundError as exc:
            raise ExecutorError(str(exc), status_code=404) from exc

    def doc_render(self, doc_id: str, upload_images: bool) -> dict:
        from app.services.block_registry import RenderContext
        from app.services.mbdoc_storage import MBDocNotFoundError
        from app.services.render_for_wechat import render_for_wechat

        try:
            doc = self._storage().get(doc_id)
        except MBDocNotFoundError as exc:
            raise ExecutorError(str(exc), status_code=404) from exc

        uploader = None
        if upload_images:
            from app.services.wechat_service import upload_image_to_wechat

            uploader = upload_image_to_wechat

        try:
            html = render_for_wechat(doc, RenderContext(upload_images=upload_images, image_uploader=uploader))
        except Exception as exc:
            raise ExecutorError(f"render failed: {exc}", status_code=500) from exc
        return {"html": html, "upload_images": upload_images}

    # image ---------------------------------------------------------------

    def image_list(self) -> list[dict]:
        from app.services import image_service

        return image_service.list_images()

    def image_upload(self, file_path: Path) -> dict:
        from app.services import image_service

        content = file_path.read_bytes()
        return image_service.upload_image(file_path.name, content)

    def image_delete(self, image_id: str) -> None:
        from app.core.exceptions import AppError
        from app.services import image_service

        try:
            image_service.delete_image(image_id)
        except AppError as exc:
            raise ExecutorError(exc.message, status_code=exc.code) from exc

    # render --------------------------------------------------------------

    def render_preview(self, html: str, css: str) -> dict:
        from app.services.legacy_render_pipeline import preview_html

        return {"html": preview_html(html, css)}

    def render_article(self, article_id: str) -> dict:
        from app.services import article_service
        from app.services.legacy_render_pipeline import process_for_wechat

        article = self.article_get(article_id)
        processed = process_for_wechat(article.get("html", ""), article.get("css", ""))
        return {"html": processed, "css": "", "title": article.get("title", "")}

    # publish -------------------------------------------------------------

    def publish_process(self, article_id: str, author: str, digest: str) -> dict:
        from app.services.publish_adapter import process_article_html

        return {"html": process_article_html(article_id)}

    def publish_draft(self, article_id: str, author: str, digest: str) -> dict:
        from app.services.publish_adapter import publish_draft_sync

        try:
            return publish_draft_sync(article_id, author or "", digest or "")
        except Exception as exc:
            raise ExecutorError(f"publish failed: {exc}", status_code=500) from exc

    # config --------------------------------------------------------------

    def config_get(self) -> dict:
        from app.services.wechat_service import load_config

        data = load_config()
        return {"appid": data.get("appid", ""), "has_secret": bool(data.get("appsecret"))}

    def config_set(self, appid: str, appsecret: str) -> dict:
        from app.services.wechat_service import save_config

        save_config(appid, appsecret)
        return {"appid": appid, "has_secret": bool(appsecret)}

    def config_check(self, appid: str, appsecret: str) -> dict:
        from app.services.wechat_service import _token_cache, get_access_token, save_config

        save_config(appid, appsecret)
        _token_cache["access_token"] = ""
        _token_cache["expires_at"] = 0
        try:
            token = get_access_token(force_refresh=True)
        except Exception as exc:
            raise ExecutorError(f"credentials rejected: {exc}", status_code=400) from exc
        return {"ok": True, "token_prefix": token[:8]}

    # projection ----------------------------------------------------------

    def article_project_to_doc(self, article_id: str, persist: bool) -> dict:
        from app.services.document_projector import article_to_mbdoc, projection_metadata_for

        article = self.article_get(article_id)
        doc = article_to_mbdoc(article)
        if persist:
            self._storage().save(doc)
        payload = doc.model_dump(mode="json")
        payload["projection"] = projection_metadata_for(doc)
        return payload


# ---------------------------------------------------------------------------
# HttpExecutor
# ---------------------------------------------------------------------------


@dataclass
class HttpExecutor:
    """Executes CLI operations by calling the running FastAPI backend."""

    settings: CLISettings
    mode: str = "http"

    def _url(self, path: str) -> str:
        return f"{self.settings.base_url.rstrip('/')}/{path.lstrip('/')}"

    def _request(self, method: str, path: str, **kwargs: Any) -> dict:
        try:
            with httpx.Client(timeout=self.settings.timeout) as client:
                response = client.request(method, self._url(path), **kwargs)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise ExecutorError(f"http error: {exc}", status_code=500) from exc
        if payload.get("code", 1) != 0:
            raise ExecutorError(payload.get("message", "request failed"), status_code=payload.get("code"))
        return payload

    def _data(self, payload: dict) -> Any:
        return payload.get("data")

    # article --------------------------------------------------------------

    def article_list(self) -> list[dict]:
        return self._data(self._request("GET", "/articles")) or []

    def article_get(self, article_id: str) -> dict:
        return self._data(self._request("GET", f"/articles/{article_id}")) or {}

    def article_create(self, title: str, mode: str) -> dict:
        return self._data(self._request("POST", "/articles", json={"title": title, "mode": mode})) or {}

    def article_update(self, article_id: str, updates: dict) -> dict:
        return self._data(self._request("PUT", f"/articles/{article_id}", json=updates)) or {}

    def article_delete(self, article_id: str) -> None:
        self._request("DELETE", f"/articles/{article_id}")

    # doc -----------------------------------------------------------------

    def doc_list(self) -> list[str]:
        data = self._data(self._request("GET", "/mbdoc")) or []
        if data and isinstance(data[0], dict):
            return [item.get("id", "") for item in data if item.get("id")]
        return list(data)

    def doc_get(self, doc_id: str) -> dict:
        return self._data(self._request("GET", f"/mbdoc/{doc_id}")) or {}

    def doc_create(self, doc_json: dict) -> dict:
        return self._data(self._request("POST", "/mbdoc", json=doc_json)) or {}

    def doc_update(self, doc_id: str, doc_json: dict) -> dict:
        return self._data(self._request("PUT", f"/mbdoc/{doc_id}", json=doc_json)) or {}

    def doc_delete(self, doc_id: str) -> None:
        self._request("DELETE", f"/mbdoc/{doc_id}")

    def doc_render(self, doc_id: str, upload_images: bool) -> dict:
        params = {"upload_images": str(upload_images).lower()}
        return self._data(self._request("POST", f"/mbdoc/{doc_id}/render", params=params)) or {}

    # image ---------------------------------------------------------------

    def image_list(self) -> list[dict]:
        return self._data(self._request("GET", "/images")) or []

    def image_upload(self, file_path: Path) -> dict:
        with file_path.open("rb") as handle:
            files = {"file": (file_path.name, handle)}
            return self._data(self._request("POST", "/images/upload", files=files)) or {}

    def image_delete(self, image_id: str) -> None:
        self._request("DELETE", f"/images/{image_id}")

    # render --------------------------------------------------------------

    def render_preview(self, html: str, css: str) -> dict:
        return self._data(self._request("POST", "/publish/preview", json={"html": html, "css": css})) or {}

    def render_article(self, article_id: str) -> dict:
        return self._data(self._request("GET", f"/publish/html/{article_id}")) or {}

    # publish -------------------------------------------------------------

    def publish_process(self, article_id: str, author: str, digest: str) -> dict:
        body = {"article_id": article_id, "author": author, "digest": digest}
        return self._data(self._request("POST", "/publish/process", json=body)) or {}

    def publish_draft(self, article_id: str, author: str, digest: str) -> dict:
        body = {"article_id": article_id, "author": author, "digest": digest}
        return self._data(self._request("POST", "/publish/draft", json=body)) or {}

    # config --------------------------------------------------------------

    def config_get(self) -> dict:
        return self._data(self._request("GET", "/config")) or {}

    def config_set(self, appid: str, appsecret: str) -> dict:
        return self._data(self._request("PUT", "/config", json={"appid": appid, "appsecret": appsecret})) or {}

    def config_check(self, appid: str, appsecret: str) -> dict:
        return self._data(self._request("POST", "/config/test", json={"appid": appid, "appsecret": appsecret})) or {}

    # projection ----------------------------------------------------------

    def article_project_to_doc(self, article_id: str, persist: bool) -> dict:
        params = {"persist": str(persist).lower()}
        return self._data(
            self._request("POST", f"/mbdoc/project/article/{article_id}", params=params)
        ) or {}


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def build_executor(settings: CLISettings) -> Executor:
    if settings.mode == "http":
        return HttpExecutor(settings=settings)
    if settings.mode == "direct":
        return DirectExecutor(settings=settings)
    raise ValueError(f"unknown CLI mode: {settings.mode!r} (expected 'direct' or 'http')")
