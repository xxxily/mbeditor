"""BlockRegistry — routes blocks to their registered renderers.

Stage 1 exposes only the core registry operations (register/find/
render_block) and the RenderContext dataclass. The default factory
``BlockRegistry.default()`` that wires up the full Stage-1 renderer set
is added in Task 4 once HeadingRenderer and ParagraphRenderer exist.
"""
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional

from app.models.mbdoc import Block, BlockType
from app.services.renderers.base import BlockRenderer


class UnknownBlockTypeError(Exception):
    """Raised when no renderer is registered for a given BlockType."""

    def __init__(self, block_type: BlockType):
        self.block_type = block_type
        super().__init__(
            f"No renderer registered for block type {block_type.value!r}. "
            f"Did you forget to register it in BlockRegistry.default()?"
        )


ImageUploader = Callable[[bytes, str], str]
"""Callable that uploads image bytes and returns a public URL.

Signature: ``(image_bytes, filename) -> url``

Used by renderers to swap local/external image URLs with WeChat CDN URLs
when ``ctx.upload_images = True``.
"""


@dataclass
class RenderContext:
    """Context passed to every block renderer.

    Attributes:
        upload_images: when True, renderers should replace local/external
            image src with uploaded CDN URLs (via ``image_uploader``). When
            False, renderers leave src unchanged.
        image_uploader: optional callable; required when ``upload_images``
            is True.
        per_block_metadata: scratchpad for renderers to share info across
            the document (e.g. a markdown renderer may record extracted
            images for the next block to reuse).
    """

    upload_images: bool = False
    image_uploader: Optional[ImageUploader] = None
    per_block_metadata: Dict[str, object] = field(default_factory=dict)


class BlockRegistry:
    """Maps BlockType → BlockRenderer and dispatches render calls."""

    def __init__(self) -> None:
        self._renderers: Dict[BlockType, BlockRenderer] = {}

    def register(self, renderer: BlockRenderer) -> None:
        self._renderers[renderer.block_type] = renderer

    def find(self, block_type: BlockType) -> BlockRenderer:
        r = self._renderers.get(block_type)
        if r is None:
            raise UnknownBlockTypeError(block_type)
        return r

    def render_block(self, block: Block, ctx: RenderContext) -> str:
        renderer = self.find(block.type)
        return renderer.render(block, ctx)
