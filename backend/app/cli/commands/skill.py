from __future__ import annotations

from importlib import resources

import typer

from app.cli.formatters import emit, emit_success
from app.cli.state import CLISettings

app = typer.Typer(help="Print the bundled agent skill guide.")


def _settings(ctx: typer.Context) -> CLISettings:
    return ctx.obj


def _read_skill() -> str:
    return resources.files("app.cli").joinpath("SKILL.md").read_text(encoding="utf-8")


@app.callback(invoke_without_command=True)
def show_skill(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is not None:
        return
    settings = _settings(ctx)
    text = _read_skill()
    if settings.json_output:
        emit_success(settings, "skill.show", {"skill": text})
        return
    emit(settings, text)


@app.command("path")
def skill_path(ctx: typer.Context) -> None:
    """Show the filesystem path of the bundled SKILL.md."""
    settings = _settings(ctx)
    path = resources.files("app.cli").joinpath("SKILL.md")
    emit_success(settings, "skill.path", {"path": str(path)})
