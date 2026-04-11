"""Tests for MBDoc Pydantic schema."""
import json
import pytest
from pydantic import ValidationError

from app.models.mbdoc import (
    MBDoc,
    MBDocMeta,
    BlockType,
    HeadingBlock,
    ParagraphBlock,
    MarkdownBlock,
    HtmlBlock,
    ImageBlock,
    SvgBlock,
    RasterBlock,
)


def test_heading_block_basic():
    block = HeadingBlock(id="b1", level=1, text="Hello")
    assert block.type == BlockType.HEADING
    assert block.level == 1


def test_heading_level_validation():
    with pytest.raises(ValidationError):
        HeadingBlock(id="b1", level=7, text="Hello")  # max is 6


def test_paragraph_block():
    block = ParagraphBlock(id="b2", text="World")
    assert block.type == BlockType.PARAGRAPH


def test_markdown_block():
    block = MarkdownBlock(id="b3", source="## Heading\n\nbody")
    assert block.type == BlockType.MARKDOWN


def test_html_block():
    block = HtmlBlock(id="b4", source="<section>hi</section>")
    assert block.type == BlockType.HTML


def test_image_block():
    block = ImageBlock(id="b5", src="/images/x.png", alt="x")
    assert block.type == BlockType.IMAGE


def test_svg_block():
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" fill="red"/></svg>'
    block = SvgBlock(id="b6", source=svg)
    assert block.type == BlockType.SVG


def test_raster_block():
    block = RasterBlock(
        id="b7",
        html='<div style="display:grid;">x</div>',
        css=".x{color:red;}",
    )
    assert block.type == BlockType.RASTER


def test_mbdoc_empty():
    doc = MBDoc(id="doc1", meta=MBDocMeta(title="Test"))
    assert doc.version == "1"
    assert doc.blocks == []


def test_mbdoc_with_blocks():
    doc = MBDoc(
        id="doc1",
        meta=MBDocMeta(title="T"),
        blocks=[
            HeadingBlock(id="b1", level=1, text="H"),
            ParagraphBlock(id="b2", text="P"),
        ],
    )
    assert len(doc.blocks) == 2
    assert doc.blocks[0].type == BlockType.HEADING
    assert doc.blocks[1].type == BlockType.PARAGRAPH


def test_mbdoc_json_roundtrip():
    doc = MBDoc(
        id="doc1",
        meta=MBDocMeta(title="T", author="Anson"),
        blocks=[
            HeadingBlock(id="b1", level=2, text="Greet"),
            ImageBlock(id="b2", src="/a.png"),
        ],
    )
    s = doc.model_dump_json()
    parsed = json.loads(s)
    assert parsed["id"] == "doc1"
    assert parsed["blocks"][0]["type"] == "heading"
    assert parsed["blocks"][1]["type"] == "image"
    # Roundtrip
    doc2 = MBDoc.model_validate(parsed)
    assert doc2.id == doc.id
    assert len(doc2.blocks) == 2


def test_mbdoc_discriminated_union_parsing():
    """Parsing raw JSON into MBDoc should pick the right Block subclass."""
    payload = {
        "id": "doc1",
        "version": "1",
        "meta": {"title": "T"},
        "blocks": [
            {"id": "b1", "type": "heading", "level": 1, "text": "H"},
            {"id": "b2", "type": "paragraph", "text": "P"},
            {"id": "b3", "type": "image", "src": "/a.png"},
        ],
    }
    doc = MBDoc.model_validate(payload)
    assert isinstance(doc.blocks[0], HeadingBlock)
    assert isinstance(doc.blocks[1], ParagraphBlock)
    assert isinstance(doc.blocks[2], ImageBlock)
