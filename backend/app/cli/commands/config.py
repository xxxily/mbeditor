from __future__ import annotations

import typer

from app.cli.executor import ExecutorError, build_executor
from app.cli.formatters import emit_error, emit_success
from app.cli.state import CLISettings

app = typer.Typer(help="Inspect or update WeChat config.")


def _settings(ctx: typer.Context) -> CLISettings:
    return ctx.obj


@app.command("get")
def get_config(ctx: typer.Context) -> None:
    settings = _settings(ctx)
    try:
        data = build_executor(settings).config_get()
    except ExecutorError as exc:
        emit_error(settings, "config.get", str(exc))
    emit_success(settings, "config.get", data)


@app.command("set")
def set_config(ctx: typer.Context, appid: str, appsecret: str) -> None:
    settings = _settings(ctx)
    try:
        data = build_executor(settings).config_set(appid, appsecret)
    except ExecutorError as exc:
        emit_error(settings, "config.set", str(exc))
    emit_success(settings, "config.set", data)


@app.command("check")
def check_config(ctx: typer.Context, appid: str, appsecret: str) -> None:
    settings = _settings(ctx)
    try:
        data = build_executor(settings).config_check(appid, appsecret)
    except ExecutorError as exc:
        emit_error(settings, "config.check", str(exc))
    emit_success(settings, "config.check", data)
