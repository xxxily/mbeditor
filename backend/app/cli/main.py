from __future__ import annotations

import os

import typer

from app.cli.commands.article import app as article_app
from app.cli.commands.config import app as config_app
from app.cli.commands.doc import app as doc_app
from app.cli.commands.image import app as image_app
from app.cli.commands.info import app as info_app
from app.cli.commands.publish import app as publish_app
from app.cli.commands.render import app as render_app
from app.cli.commands.skill import app as skill_app
from app.cli.state import CLISettings
from pathlib import Path as _Path


def _apply_data_dir(raw: str) -> None:
    if not raw:
        return
    from app.core import config as config_mod

    root = _Path(raw).expanduser().resolve()
    config_mod.settings.IMAGES_DIR = str(root / "images")
    config_mod.settings.ARTICLES_DIR = str(root / "articles")
    config_mod.settings.MBDOCS_DIR = str(root / "mbdocs")
    config_mod.settings.CONFIG_FILE = str(root / "config.json")

app = typer.Typer(
    help=(
        "MBEditor - agent-first CLI for WeChat article authoring.\n\n"
        "Default mode is 'direct' (local file-backed services, no backend "
        "required). Use --mode http to route through a running FastAPI "
        "server; required for WeChat-touching operations (publish draft, "
        "config check) unless the CLI has direct access to WeChat credentials."
    ),
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    rich_markup_mode=None,
)

app.add_typer(article_app, name="article", help="Legacy Article CRUD.")
app.add_typer(doc_app, name="doc", help="MBDoc CRUD and render.")
app.add_typer(image_app, name="image", help="Image library operations.")
app.add_typer(render_app, name="render", help="Render preview / article / doc HTML.")
app.add_typer(publish_app, name="publish", help="Process or publish to WeChat.")
app.add_typer(config_app, name="config", help="WeChat credential config.")
app.add_typer(skill_app, name="skill", help="Print the bundled agent skill guide.")
app.add_typer(info_app, name="info", help="Runtime info (version, paths, mode).")


@app.callback()
def main(
    ctx: typer.Context,
    base_url: str = typer.Option(
        os.environ.get("MBEDITOR_BASE_URL", "http://127.0.0.1:7072/api/v1"),
        "--base-url",
        help="API base URL (used only in --mode http).",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    compact_json: bool = typer.Option(False, "--compact", help="Emit single-line JSON (with --json)."),
    timeout: float = typer.Option(30.0, "--timeout", min=1.0, help="HTTP timeout seconds."),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress non-error output."),
    mode: str = typer.Option(
        os.environ.get("MBEDITOR_MODE", "direct"),
        "--mode",
        case_sensitive=False,
        help="Executor mode: 'direct' (local, default) or 'http' (via running backend).",
    ),
    data_dir: str = typer.Option(
        os.environ.get("MBEDITOR_DATA_DIR", ""),
        "--data-dir",
        help=(
            "Override the data directory used in direct mode. Expects "
            "subdirs 'articles/', 'mbdocs/', 'images/', and a 'config.json' file."
        ),
    ),
) -> None:
    mode_lower = mode.lower()
    if mode_lower not in {"direct", "http"}:
        raise typer.BadParameter(f"--mode must be 'direct' or 'http', got {mode!r}")

    _apply_data_dir(data_dir)

    ctx.obj = CLISettings(
        base_url=base_url,
        json_output=json_output,
        compact_json=compact_json,
        timeout=timeout,
        quiet=quiet,
        mode=mode_lower,
        data_dir=data_dir or None,
    )


if __name__ == "__main__":
    app()
