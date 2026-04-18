from __future__ import annotations

import typer

from app.cli.formatters import emit_success
from app.cli.state import CLISettings
from app.core.config import APP_VERSION, settings as app_settings

app = typer.Typer(help="Runtime info: version, mode, data paths.")


def _settings(ctx: typer.Context) -> CLISettings:
    return ctx.obj


@app.callback(invoke_without_command=True)
def show_info(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is not None:
        return
    cli_settings = _settings(ctx)
    data = {
        "version": APP_VERSION,
        "mode": cli_settings.mode,
        "base_url": cli_settings.base_url,
        "timeout": cli_settings.timeout,
        "data_dir": cli_settings.data_dir,
        "paths": {
            "articles": app_settings.ARTICLES_DIR,
            "mbdocs": app_settings.MBDOCS_DIR,
            "images": app_settings.IMAGES_DIR,
            "config": app_settings.CONFIG_FILE,
        },
    }
    emit_success(cli_settings, "info", data)


@app.command("version")
def show_version(ctx: typer.Context) -> None:
    cli_settings = _settings(ctx)
    emit_success(cli_settings, "info.version", {"version": APP_VERSION})


@app.command("paths")
def show_paths(ctx: typer.Context) -> None:
    cli_settings = _settings(ctx)
    emit_success(
        cli_settings,
        "info.paths",
        {
            "articles": app_settings.ARTICLES_DIR,
            "mbdocs": app_settings.MBDOCS_DIR,
            "images": app_settings.IMAGES_DIR,
            "config": app_settings.CONFIG_FILE,
        },
    )
