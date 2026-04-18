from __future__ import annotations

import typer

from app.cli.executor import ExecutorError, build_executor
from app.cli.formatters import emit_error, emit_success
from app.cli.state import CLISettings

app = typer.Typer(help="Render preview or final HTML.")


def _settings(ctx: typer.Context) -> CLISettings:
    return ctx.obj


@app.command("preview")
def preview_html(
    ctx: typer.Context,
    html: str,
    css: str = typer.Argument("", help="Optional CSS to inline into the preview."),
) -> None:
    settings = _settings(ctx)
    try:
        data = build_executor(settings).render_preview(html, css)
    except ExecutorError as exc:
        emit_error(settings, "render.preview", str(exc))
    emit_success(settings, "render.preview", data)


@app.command("article")
def render_article(ctx: typer.Context, article_id: str) -> None:
    settings = _settings(ctx)
    try:
        data = build_executor(settings).render_article(article_id)
    except ExecutorError as exc:
        emit_error(settings, "render.article", str(exc), {"id": article_id})
    emit_success(settings, "render.article", data)


@app.command("doc")
def render_doc(
    ctx: typer.Context,
    mbdoc_id: str,
    upload_images: bool = typer.Option(False, "--upload-images/--no-upload-images"),
) -> None:
    settings = _settings(ctx)
    try:
        data = build_executor(settings).doc_render(mbdoc_id, upload_images)
    except ExecutorError as exc:
        emit_error(settings, "render.doc", str(exc), {"id": mbdoc_id})
    emit_success(settings, "render.doc", data)
