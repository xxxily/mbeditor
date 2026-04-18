import json
from typing import Any

import typer

from app.cli.state import CLISettings


def _render_json(settings: CLISettings, payload: Any) -> str:
    if settings.compact_json:
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return json.dumps(payload, ensure_ascii=False, indent=2)


def emit(settings: CLISettings, payload: Any, *, force: bool = False) -> None:
    if settings.quiet and not force:
        return
    if settings.json_output:
        typer.echo(_render_json(settings, payload))
        return
    if isinstance(payload, str):
        typer.echo(payload)
        return
    typer.echo(_render_json(settings, payload))


def emit_success(settings: CLISettings, action: str, data: Any = None, message: str = "success") -> None:
    emit(settings, {"ok": True, "action": action, "message": message, "data": data})


def emit_error(settings: CLISettings, action: str, message: str, data: Any = None, exit_code: int = 1) -> None:
    emit(
        settings,
        {"ok": False, "action": action, "message": message, "data": data},
        force=True,
    )
    raise typer.Exit(exit_code)
