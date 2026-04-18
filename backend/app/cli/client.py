from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from app.cli.state import CLISettings


class CLIClient:
    def __init__(self, settings: CLISettings):
        self.settings = settings

    def _url(self, path: str) -> str:
        return f"{self.settings.base_url.rstrip('/')}/{path.lstrip('/')}"

    def _unwrap(self, response: httpx.Response) -> dict[str, Any]:
        response.raise_for_status()
        payload = response.json()
        if payload.get("code", 1) != 0:
            raise RuntimeError(payload.get("message", "request failed"))
        return payload

    def request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        with httpx.Client(timeout=self.settings.timeout) as client:
            response = client.request(method, self._url(path), **kwargs)
        return self._unwrap(response)

    def get(self, path: str, **kwargs: Any) -> dict[str, Any]:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> dict[str, Any]:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> dict[str, Any]:
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> dict[str, Any]:
        return self.request("DELETE", path, **kwargs)

    def post_file(self, path: str, file_path: Path, field_name: str = "file") -> dict[str, Any]:
        with file_path.open("rb") as handle:
            files = {field_name: (file_path.name, handle)}
            return self.post(path, files=files)
