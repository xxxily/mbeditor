from __future__ import annotations

from typing import Optional

import typer

from app.cli.executor import ExecutorError, build_executor
from app.cli.formatters import emit_error, emit_success
from app.cli.state import CLISettings

app = typer.Typer(help="Manage legacy Article resources.")


def _settings(ctx: typer.Context) -> CLISettings:
    return ctx.obj


@app.command("list")
def list_articles(ctx: typer.Context) -> None:
    settings = _settings(ctx)
    try:
        data = build_executor(settings).article_list()
    except ExecutorError as exc:
        emit_error(settings, "article.list", str(exc))
    emit_success(settings, "article.list", data)


@app.command("get")
def get_article(ctx: typer.Context, article_id: str) -> None:
    settings = _settings(ctx)
    try:
        data = build_executor(settings).article_get(article_id)
    except ExecutorError as exc:
        emit_error(settings, "article.get", str(exc), {"id": article_id})
    emit_success(settings, "article.get", data)


@app.command("create")
def create_article(
    ctx: typer.Context,
    title: str,
    mode: str = typer.Argument("html", help="Content mode: 'html' or 'markdown'."),
) -> None:
    settings = _settings(ctx)
    try:
        data = build_executor(settings).article_create(title, mode)
    except ExecutorError as exc:
        emit_error(settings, "article.create", str(exc), {"title": title, "mode": mode})
    emit_success(settings, "article.create", data)


@app.command("update")
def update_article(
    ctx: typer.Context,
    article_id: str,
    title: Optional[str] = typer.Option(None),
    mode: Optional[str] = typer.Option(None),
    html: Optional[str] = typer.Option(None),
    css: Optional[str] = typer.Option(None),
    js: Optional[str] = typer.Option(None),
    markdown: Optional[str] = typer.Option(None),
    cover: Optional[str] = typer.Option(None),
    author: Optional[str] = typer.Option(None),
    digest: Optional[str] = typer.Option(None),
) -> None:
    settings = _settings(ctx)
    updates = {
        key: value
        for key, value in {
            "title": title,
            "mode": mode,
            "html": html,
            "css": css,
            "js": js,
            "markdown": markdown,
            "cover": cover,
            "author": author,
            "digest": digest,
        }.items()
        if value is not None
    }
    if not updates:
        emit_error(settings, "article.update", "no update fields provided", {"id": article_id}, exit_code=2)
    try:
        data = build_executor(settings).article_update(article_id, updates)
    except ExecutorError as exc:
        emit_error(settings, "article.update", str(exc), {"id": article_id})
    emit_success(settings, "article.update", data)


@app.command("delete")
def delete_article(ctx: typer.Context, article_id: str) -> None:
    settings = _settings(ctx)
    try:
        build_executor(settings).article_delete(article_id)
    except ExecutorError as exc:
        emit_error(settings, "article.delete", str(exc), {"id": article_id})
    emit_success(settings, "article.delete", {"id": article_id})


@app.command("project-to-doc")
def project_article_to_doc(
    ctx: typer.Context,
    article_id: str,
    persist: bool = typer.Option(False, "--persist/--no-persist"),
) -> None:
    settings = _settings(ctx)
    try:
        data = build_executor(settings).article_project_to_doc(article_id, persist)
    except ExecutorError as exc:
        emit_error(settings, "article.project-to-doc", str(exc), {"id": article_id})
    emit_success(settings, "article.project-to-doc", data)
