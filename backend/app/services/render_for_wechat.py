"""
render_for_wechat — the single canonical rendering entry point.

This function is the SINGLE source of truth for converting an MBDoc into
WeChat-compatible HTML. Preview iframe, "copy rich text", and "push to
draft" all call this function. The diff between ``upload_images=False``
and ``upload_images=True`` calls MUST be confined to ``<img src>``
attributes; this invariant is verified in
``tests/test_render_for_wechat.py``.

The registry now wires real renderers for all current built-in block types.
Future work extends renderer behavior, but this function remains the single
orchestrator and does not change.
"""
from typing import Optional

from app.models.mbdoc import MBDoc
from app.services.block_registry import BlockRegistry, RenderContext


async def render_for_wechat(
    doc: MBDoc,
    ctx: RenderContext,
    *,
    registry: Optional[BlockRegistry] = None,
) -> str:
    reg = registry or BlockRegistry.default()
    pieces: list[str] = []
    for block in doc.blocks:
        pieces.append(await reg.render_block(block, ctx))
    return "\n".join(pieces)
