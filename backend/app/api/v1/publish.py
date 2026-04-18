import asyncio
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.response import success
from app.services import article_service, publish_adapter

router = APIRouter(prefix="/publish", tags=["publish"])


class PublishDraftReq(BaseModel):
    article_id: str
    author: Optional[str] = ""
    digest: Optional[str] = ""


class PreviewReq(BaseModel):
    html: str
    css: str = ""


# Minimal router layer - all functionality moved to publish_adapter service
# This file is intentionally thin to follow single-responsibility principle

@router.get("/html/{article_id}")
async def get_processed_html(article_id: str):
    """Get article HTML with CSS inlined - ready for copying to WeChat."""
    article = article_service.get_article(article_id)
    processed = publish_adapter.process_for_wechat(
        article.get("html", ""),
        article.get("css", ""),
    )
    return success({"html": processed, "css": "", "title": article.get("title", "")})


@router.post("/preview")
async def preview_wechat(req: PreviewReq):
    """Process raw HTML+CSS for WeChat - no save needed."""
    processed = publish_adapter.preview_html(req.html, req.css)
    return success({"html": processed})


@router.post("/process")
async def process_article(req: PublishDraftReq):
    """Process article: inline CSS + replace local images with WeChat CDN URLs."""
    processed = publish_adapter.process_article_html(req.article_id)
    return success({"html": processed})


@router.post("/process-for-copy")
async def process_html_for_copy(req: PreviewReq):
    """Process raw HTML+CSS for copy, including image upload when configured."""
    processed = publish_adapter.process_html_for_copy(req.html, req.css)
    return success({"html": processed})


@router.post("/draft")
async def publish_draft(req: PublishDraftReq):
    """Push article to WeChat draft box with CSS inlined."""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        publish_adapter.publish_draft_sync,
        req.article_id,
        req.author or "",
        req.digest or "",
    )
    return success(result)
