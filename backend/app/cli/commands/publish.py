from __future__ import annotations

import typer

from app.cli.executor import ExecutorError, build_executor
from app.cli.formatters import emit_error, emit_success
from app.cli.state import CLISettings

app = typer.Typer(help="Process or publish content through WeChat APIs.")


def _settings(ctx: typer.Context) -> CLISettings:
    return ctx.obj


@app.command("process")
def process_article(
    ctx: typer.Context,
    article_id: str,
    author: str = typer.Argument(""),
    digest: str = typer.Argument(""),
) -> None:
    settings = _settings(ctx)
    try:
        data = build_executor(settings).publish_process(article_id, author, digest)
    except ExecutorError as exc:
        emit_error(settings, "publish.process", str(exc), {"id": article_id})
    emit_success(settings, "publish.process", data)


@app.command("draft")
def publish_draft(
    ctx: typer.Context,
    article_id: str,
    author: str = typer.Argument(""),
    digest: str = typer.Argument(""),
) -> None:
    settings = _settings(ctx)
    try:
        data = build_executor(settings).publish_draft(article_id, author, digest)
    except ExecutorError as exc:
        emit_error(settings, "publish.draft", str(exc), {"id": article_id})
    emit_success(settings, "publish.draft", data)
