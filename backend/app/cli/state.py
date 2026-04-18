from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class CLISettings:
    """Root CLI settings passed down through typer.Context."""

    base_url: str = "http://127.0.0.1:7072/api/v1"
    json_output: bool = False
    compact_json: bool = False
    timeout: float = 30.0
    quiet: bool = False
    mode: str = "direct"
    data_dir: Optional[str] = None
