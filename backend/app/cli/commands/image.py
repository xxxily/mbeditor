from __future__ import annotations

from pathlib import Path

import typer

from app.cli.executor import ExecutorError, build_executor
from app.cli.formatters import emit_error, emit_success
from app.cli.state import CLISettings

app = typer.Typer(help="Manage image library records.")


def _settings(ctx: typer.Context) -> CLISettings:
    return ctx.obj


@app.command("list")
def list_images(ctx: typer.Context) -> None:
    settings = _settings(ctx)
    try:
        data = build_executor(settings).image_list()
    except ExecutorError as exc:
        emit_error(settings, "image.list", str(exc))
    emit_success(settings, "image.list", data)


@app.command("upload")
def upload_image(ctx: typer.Context, file: Path) -> None:
    settings = _settings(ctx)
    if not file.exists():
        emit_error(settings, "image.upload", f"file not found: {file}", {"file": str(file)}, exit_code=2)
    try:
        data = build_executor(settings).image_upload(file)
    except ExecutorError as exc:
        emit_error(settings, "image.upload", str(exc), {"file": str(file)})
    emit_success(settings, "image.upload", data)


@app.command("delete")
def delete_image(ctx: typer.Context, image_id: str) -> None:
    settings = _settings(ctx)
    try:
        build_executor(settings).image_delete(image_id)
    except ExecutorError as exc:
        emit_error(settings, "image.delete", str(exc), {"id": image_id})
    emit_success(settings, "image.delete", {"id": image_id})
