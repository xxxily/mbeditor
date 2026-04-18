from __future__ import annotations

import json
from pathlib import Path

import typer

from app.cli.executor import ExecutorError, build_executor
from app.cli.formatters import emit_error, emit_success
from app.cli.state import CLISettings

app = typer.Typer(help="Manage MBDoc resources.")


def _settings(ctx: typer.Context) -> CLISettings:
    return ctx.obj


def _load_json_file(settings: CLISettings, file: Path, action: str) -> dict:
    try:
        return json.loads(file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        emit_error(settings, action, f"cannot read JSON from {file}: {exc}", {"file": str(file)})


@app.command("list")
def list_docs(ctx: typer.Context) -> None:
    settings = _settings(ctx)
    try:
        data = build_executor(settings).doc_list()
    except ExecutorError as exc:
        emit_error(settings, "doc.list", str(exc))
    emit_success(settings, "doc.list", data)


@app.command("get")
def get_doc(ctx: typer.Context, mbdoc_id: str) -> None:
    settings = _settings(ctx)
    try:
        data = build_executor(settings).doc_get(mbdoc_id)
    except ExecutorError as exc:
        emit_error(settings, "doc.get", str(exc), {"id": mbdoc_id})
    emit_success(settings, "doc.get", data)


@app.command("create")
def create_doc(ctx: typer.Context, file: Path) -> None:
    settings = _settings(ctx)
    doc_json = _load_json_file(settings, file, "doc.create")
    try:
        data = build_executor(settings).doc_create(doc_json)
    except ExecutorError as exc:
        emit_error(settings, "doc.create", str(exc), {"file": str(file)})
    emit_success(settings, "doc.create", data)


@app.command("update")
def update_doc(ctx: typer.Context, mbdoc_id: str, file: Path) -> None:
    settings = _settings(ctx)
    doc_json = _load_json_file(settings, file, "doc.update")
    try:
        data = build_executor(settings).doc_update(mbdoc_id, doc_json)
    except ExecutorError as exc:
        emit_error(settings, "doc.update", str(exc), {"id": mbdoc_id, "file": str(file)})
    emit_success(settings, "doc.update", data)


@app.command("delete")
def delete_doc(ctx: typer.Context, mbdoc_id: str) -> None:
    settings = _settings(ctx)
    try:
        build_executor(settings).doc_delete(mbdoc_id)
    except ExecutorError as exc:
        emit_error(settings, "doc.delete", str(exc), {"id": mbdoc_id})
    emit_success(settings, "doc.delete", {"id": mbdoc_id})


@app.command("render")
def render_doc(
    ctx: typer.Context,
    mbdoc_id: str,
    upload_images: bool = typer.Option(False, "--upload-images/--no-upload-images"),
) -> None:
    settings = _settings(ctx)
    try:
        data = build_executor(settings).doc_render(mbdoc_id, upload_images)
    except ExecutorError as exc:
        emit_error(settings, "doc.render", str(exc), {"id": mbdoc_id})
    emit_success(settings, "doc.render", data)
