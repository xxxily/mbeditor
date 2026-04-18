# Backend MBDoc Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Migrate backend document handling from the legacy `Article + publish.py` pipeline to an `MBDoc`-centered architecture without breaking current article CRUD, preview, copy, or WeChat draft push.

**Architecture:** Keep legacy `Article` as an external compatibility shell for one transition period, but move document truth, render truth, and image/upload semantics behind `MBDoc`, `BlockRegistry`, and a dedicated publish adapter. Split the current monolithic publish flow into composable services: storage/projection, renderers, image upload, and WeChat draft delivery.

**Tech Stack:** FastAPI, Pydantic, file-based JSON storage, Premailer, Pillow, httpx, WeChat Official Account APIs.

---

## 1. Current Backend Truth

- Legacy truth is `article_service`: flat JSON files under `ARTICLES_DIR` with `{title, mode, html, css, js, markdown, cover, author, digest}` and no schema-level validation or block semantics.
- The effective publish pipeline lives in `app/api/v1/publish.py`: CSS cleanup, premailer inline, sanitize/rewrite, image upload substitution, cover selection, source URL extraction, and final WeChat draft push are all coupled there.
- WeChat integration lives in `wechat_service`: config storage, token caching, image upload, thumb upload, HTML-wide `src=` replacement, and draft creation.
- `MBDoc` already exists as a typed model plus file storage and CRUD/render endpoints, but only `heading` and `paragraph` have real renderers. `markdown/html/image/svg/raster` still route through stub renderers.
- The intended invariant is already defined: preview/copy/publish should share one canonical render path, and `upload_images=False` vs `True` should only differ in image URLs.

## 2. Target Backend Shape

- `MBDoc` becomes the canonical document model for backend persistence and rendering.
- A new backend application layer should expose four explicit boundaries:
  - `DocumentStore`: load/save/query canonical `MBDoc`.
  - `DocumentProjector`: convert legacy `Article` payloads to/from `MBDoc` during transition.
  - `RenderPipeline`: render `MBDoc` through `BlockRegistry` into WeChat-safe HTML.
  - `PublishGateway`: upload images, resolve cover, and push the final payload to WeChat.
- `render_for_wechat(doc, ctx)` remains the single render entry point, but sanitize/inlining logic moves out of the router and behind renderer-aware services.
- Image behavior becomes block-aware: image upload is triggered by `ImageBlock` or rasterized outputs, not by global regex replacement over arbitrary HTML.
- WeChat integration becomes transport-only: token management, upload APIs, draft create APIs, and no document parsing.

## 3. Phased Migration Steps

### Phase 0: Freeze and clarify boundaries

- Stop adding new transformation logic directly to `publish.py`.
- Define `publish.py` as legacy adapter/router only.
- Codify backend invariants in tests:
  - render determinism
  - preview/publish structural parity
  - image upload diff confined to `src`
  - WeChat gateway never mutates document structure

### Phase 1: Canonicalize document storage

- Keep `Article` files for compatibility, but introduce a single canonical persistence rule for new work: all new backend-side document semantics land in `MBDoc`.
- Add a compatibility projection layer:
  - `Article -> MBDoc` for legacy preview/publish
  - optional `MBDoc -> Article summary` for list/detail compatibility
- Do not migrate article list/settings/config data yet.

### Phase 2: Extract render pipeline from router code

- Move `_inline_css`, `_sanitize_for_wechat`, and related helpers out of `publish.py` into dedicated render modules.
- Split render stages explicitly:
  - block render
  - HTML normalization/sanitization
  - WeChat-specific post-processing
- `publish.py` should call one orchestrator service, not hold transformation logic itself.

### Phase 3: Replace stubs with real renderers

- Implement block renderers in this order:
  - `HTML`: inline per-block CSS and sanitize authored HTML
  - `MARKDOWN`: markdown -> HTML -> same sanitize path
  - `IMAGE`: local/remote asset handling, width/height normalization
  - `SVG`: direct inline SVG if safe, otherwise degrade to raster path
  - `RASTER`: raster worker contract and `<img>` emission
- Keep `heading/paragraph` untouched unless parity evidence requires it.

### Phase 4: Move image handling out of regex HTML rewriting

- Replace `wechat_service.process_html_images()` as the primary mechanism with renderer-driven image resolution.
- Introduce an image pipeline with explicit steps:
  - resolve source bytes
  - normalize/convert format
  - upload/cache by content hash
  - return public WeChat URL
- Leave a legacy fallback for raw HTML blocks until all HTML/image semantics are block-aware.

### Phase 5: Isolate WeChat publishing

- Create a `WeChatDraftPublisher` boundary that accepts:
  - rendered HTML
  - title/author/digest
  - cover reference or fallback strategy
  - source URL metadata
- Keep token caching and raw API calls inside `wechat_service`, but remove HTML parsing, regex `src` replacement, and cover extraction heuristics from it over time.

### Phase 6: Flip compatibility direction

- Make `/publish/*` consume `MBDoc` first, using projection only when the source is still a legacy `Article`.
- Mark legacy article HTML/CSS fields as derived or transitional, not authoritative.
- Keep `/articles` API alive, but back it with projection where feasible.

### Phase 7: Deprecate legacy publish path

- Deprecate direct `Article.html/css` publish as a primary backend path.
- Keep read-only legacy support for old articles until migration coverage is high enough.
- Remove monolithic publish transforms only after all block types and image flows have real implementations.

## 4. Risky Files / Modules

- `backend/app/api/v1/publish.py`: largest risk surface; mixes routing, render policy, HTML surgery, image upload, cover heuristics, and draft push.
- `backend/app/services/wechat_service.py`: transport concerns and document-mutation concerns are entangled; regex image replacement is too global.
- `backend/app/services/article_service.py`: flat untyped storage keeps legacy truth alive and encourages bypassing `MBDoc`.
- `backend/app/services/block_registry.py`: current default registry hides incompleteness behind stubs; migration progress depends on this file becoming the real assembly point.
- `backend/app/services/render_for_wechat.py`: designated canonical entry point, so any bypass around it creates long-term drift.
- `backend/tests/test_sanitize_baseline.py`: appears to encode an earlier contract that no longer matches current sanitizer behavior; treat as a contract-risk indicator, not ground truth.

## 5. Recommended Cut Points

- Cut point A: router vs service
  - `publish.py` stops owning transforms and becomes a thin adapter.
- Cut point B: document model vs transport shell
  - `MBDoc` owns content truth; `Article` remains a compatibility resource.
- Cut point C: rendering vs delivery
  - render pipeline produces final HTML; WeChat gateway only uploads/sends.
- Cut point D: image resolution vs HTML mutation
  - image upload happens from block/image abstractions, not broad regex replacement.
- Cut point E: legacy compatibility vs deprecation
  - projection layer is the only allowed place where legacy article fields are interpreted.

## 6. What Should Stay Legacy for Now

- `/articles` CRUD surface and its list/detail payloads
- article list metadata shape (`id/title/mode/cover/created_at/updated_at`)
- WeChat config endpoints and token persistence
- image library endpoints under `/images`
- current file-based storage strategy in general
- existing cover/digest/author metadata model, until `MBDoc.meta` fully covers all publish needs

## Recommended Sequence

1. Freeze `publish.py` and extract render services.
2. Add `Article <-> MBDoc` projection layer.
3. Implement real `HTML` and `MARKDOWN` renderers.
4. Move image handling to renderer-driven upload services.
5. Introduce a dedicated WeChat publish gateway.
6. Switch `/publish` to `MBDoc`-first orchestration.
7. Deprecate direct legacy publish logic.
