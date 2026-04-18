# MBEditor Project Map

Last updated: 2026-04-16

## 1. What This Project Is

MBEditor is a WeChat public-account article editor built around two parallel product shapes:

1. The current production path is the legacy `Article` model:
   `article = { title, mode, html, css, js, markdown, ... }`
   Frontend pages, autosave, preview, copy, publish, settings, and image upload all still revolve around this model.
2. The next architecture is the block-based `MBDoc` model:
   `mbdoc = { id, version, meta, blocks[] }`
   This is already present in the backend as schema, storage, registry, renderer entrypoint, and CRUD/render API. `heading`, `paragraph`, `markdown`, `html`, `image`, `svg`, and `raster` now all have real renderer entries, although `raster` is still a migration-phase HTML fallback rather than the future Playwright PNG worker.

The repo is therefore not in a greenfield state and not in a completed migration state. It is a live hybrid.

## 2. Progressive Disclosure Reading Order

If you need to get productive fast in a future session, read in this order:

1. [docs/architecture/SESSION_ONRAMP.md](./SESSION_ONRAMP.md)
2. [docs/architecture/PROJECT_MAP.md](./PROJECT_MAP.md)
3. [docs/superpowers/SESSION_HANDOFF.md](../superpowers/SESSION_HANDOFF.md)
4. [docs/superpowers/plans/2026-04-11-mbeditor-wysiwyg-roadmap.md](../superpowers/plans/2026-04-11-mbeditor-wysiwyg-roadmap.md)
5. Backend entrypoints:
   `backend/app/main.py`
   `backend/app/api/v1/router.py`
   `backend/app/api/v1/publish.py`
   `backend/app/api/v1/mbdoc.py`
6. Frontend entrypoints:
   `frontend/src/pages/Editor.tsx`
   `frontend/src/components/preview/WechatPreview.tsx`
   `frontend/src/components/panel/ActionPanel.tsx`
   `frontend/src/pages/ArticleList.tsx`
7. Research docs when making architecture decisions:
   `docs/research/wechat-wysiwyg-pipeline.md`
   `docs/research/wechat-svg-capability.md`
   `docs/research/html-to-svg-compilation.md`

## 3. Repository Topology

### `backend/`

FastAPI service. This is where both the current production pipeline and the future block renderer live.

Key areas:

- `app/main.py`
  App boot, CORS, upload-size middleware, static image mount, router registration.
- `app/api/v1/articles.py`
  Legacy article CRUD.
- `app/api/v1/images.py`
  Image upload/list/delete for local image store.
- `app/api/v1/wechat.py`
  WeChat credential config endpoints.
- `app/api/v1/publish.py`
  Legacy publish pipeline. This is the current operational center for preview, HTML processing, image upload to WeChat CDN, and push to draft.
- `app/api/v1/mbdoc.py`
  New block-document CRUD and render API.
- `app/models/mbdoc.py`
  Canonical block schema for the migration target.
- `app/services/block_registry.py`
  Renderer registry plus rendering context.
- `app/services/render_for_wechat.py`
  New single-entry block render orchestrator.
- `app/services/article_service.py`
  File-backed CRUD for legacy articles.
- `app/services/image_service.py`
  Local image store with MD5 dedup and `_index.json`.
- `app/services/wechat_service.py`
  Stable token, image upload, thumb upload, draft creation, and image URL rewriting.
- `app/services/renderers/`
  Current real renderers: `heading_paragraph.py`, `html_renderer.py`, `markdown_renderer.py`, `image_renderer.py`, `svg_renderer.py`, `raster_renderer.py`
  Placeholder renderer remains in `stub.py` for future or custom block types, but the built-in 7 block types no longer use it.

### `frontend/`

React 19 + TypeScript + Vite app. Current UI is still legacy-article-first.

Key areas:

- `src/pages/ArticleList.tsx`
  Main landing page, article CRUD initiation, sample content injection.
- `src/pages/Editor.tsx`
  Main editing shell, autosave, backend preview processing, split editor/preview state, image insertion, publish modal trigger.
- `src/pages/Settings.tsx`
  WeChat config and theme/preferences UI.
- `src/components/preview/WechatPreview.tsx`
  iframe-based preview surface with editable body and semantic diff handling.
- `src/components/panel/ActionPanel.tsx`
  Copy, publish, export actions. Important seam with backend pipeline.
- `src/components/editor/MonacoEditor.tsx`
  Core text/code editor wrapper.
- `src/components/editor/WechatTiptapEditor.tsx`
  Separate visual editor experiment path. Present in codebase but not currently the main page path.
- `src/utils/markdown.ts`
  Frontend markdown-to-inline-HTML rendering.
- `src/utils/extractor.ts`
  Heuristic HTML extraction from mixed content.
- `src/utils/htmlSemantics.ts`
  Semantic normalization for editable preview round-tripping.
- `src/hooks/useClipboard.ts`
  Clipboard write helper.
- `src/hooks/useImageUpload.ts`
  Local image upload helper.

### `docs/research/`

Architecture decision evidence. These files are not implementation docs; they explain why the current roadmap exists.

### `docs/superpowers/`

Past multi-session orchestration material. Useful for historical context and prior execution flow, but not all of it matches current repo reality. Treat as guidance plus historical state, not as unquestioned truth.

### `skill/`

`skill/mbeditor.skill.md` documents the product for agent-driven use. It contains important product assumptions and also historical carryover, so it should be read alongside current code, not instead of current code.

## 4. Runtime Model

### Current runtime surfaces

- Frontend:
  `http://localhost:7073`
- Backend API:
  `http://localhost:7072/api/v1`
- Static images:
  backend mounts `/images` from `settings.IMAGES_DIR`

### Storage model

- Legacy articles:
  `data/articles/<id>.json`
- Local images:
  `data/images/...` plus `data/images/_index.json`
- New block docs:
  `data/mbdocs/<id>.json`
- WeChat credentials:
  `data/config.json`

### Deploy/dev model

- Docker compose is the primary deployment path.
- Local development is split:
  backend via `uvicorn`
  frontend via `vite`

## 5. Current Architecture in Plain Terms

### The legacy pipeline that actually powers the app now

1. Frontend editor edits an `Article`.
2. Autosave persists the article JSON via `/articles/{id}`.
3. Preview in `Editor.tsx` derives raw HTML:
   markdown mode uses `renderMarkdown`
   html mode uses `extractHTML`
4. That HTML is then sent to backend `/publish/preview`.
5. Backend `publish.py` does CSS inlining and WeChat-oriented sanitizing.
6. Frontend iframe preview renders the processed HTML.
7. Copy and publish actions call backend publish endpoints again.

This means preview/copy/publish are backend-shaped even though the UI data model is still the legacy article shape.

### The future pipeline that already exists in partial form

1. Client or agent creates an `MBDoc`.
2. `MBDoc` is stored in `data/mbdocs`.
3. `render_for_wechat(doc, ctx)` dispatches each block through a renderer.
4. Real block renderers eventually become the only source of truth.
5. Frontend editor migrates from flat article fields to block editing.

This future architecture is only partially implemented.

## 6. Backend Deep Structure

### Legacy article subsystem

- Storage is file-based, not database-backed.
- `article_service` is intentionally thin.
- `publish.py` is the highest-risk file in the repo because it mixes:
  CSS inlining
  HTML sanitation
  WeChat compatibility rewriting
  image upload orchestration
  draft push orchestration
  cover fallback generation

This file is both critical and overloaded.

### MBDoc subsystem

- `MBDoc` uses discriminated Pydantic unions for block typing.
- IDs are validated to prevent traversal and unsafe names.
- `BlockRegistry.default()` is the extension seam for migration.
- Stage 1 is implemented:
  schema
  storage
  registry
  top-level render entrypoint
  CRUD/render API
- Stage 2+ are not implemented:
  markdown/html/image/svg/raster real renderers

### WeChat integration subsystem

- Uses `stable_token`, not legacy token issuance.
- Upload image API rewrites inline `<img src>` URLs to WeChat CDN URLs.
- Draft creation optionally derives cover from article cover or first body image.
- Processing logic is regex-heavy and pragmatic rather than AST-driven.

## 7. Frontend Deep Structure

### Main UI architecture

- The app has three pages:
  article list
  editor
  settings
- `Editor.tsx` is the real center of the frontend.
- Editor has three view modes:
  code
  preview
  split
- Two content modes:
  html
  markdown

### Editor state model

The editor keeps one `Article` object in state and mutates fields directly:

- `title`
- `mode`
- `html`
- `css`
- `js`
- `markdown`

Autosave is debounced and pushes only selected fields.

### Preview model

- Raw preview HTML is derived locally.
- Processed preview HTML is requested from backend.
- `WechatPreview` writes that HTML into an iframe.
- In `wechat` mode the iframe body is editable and changes can round-trip back into `article.html`.

This is an unusual hybrid: the preview is both output surface and inline editing surface.

### Secondary/legacy/experimental surfaces

- `WechatTiptapEditor.tsx` exists but is not the main editor route in current flow.
- It suggests earlier or alternate attempts at WYSIWYG/block editing.
- The repo therefore contains active path code plus dormant or side-path code. Do not assume every component under `components/editor/` is equally alive.

## 8. Tests and Validation Reality

### Backend

Backend has meaningful tests for:

- MBDoc schema
- MBDoc storage
- block registry
- top-level block rendering
- mbdoc API
- sanitize behavior
- visual infrastructure under `backend/tests/visual/`

But the code and tests are not fully aligned. Example:

- `test_sanitize_baseline.py` says Stage 0 sanitizer should preserve `display:grid`, `position:absolute`, and `animation`
- current `publish.py` implementation still rewrites/removes many of those properties

That mismatch is an architectural fact, not a minor footnote.

### Frontend

Frontend tests are light:

- preview baseline smoke
- vitest smoke

There is much less confidence coverage on editor state flow than on backend schema flow.

### Current local verification state

At the moment this workspace does not have runtime dependencies installed:

- backend: `pytest` unavailable
- frontend: local `vitest`, `tsc`, `vite` unavailable because dependencies are not installed

So code understanding here is from source inspection, not fresh green test execution.

## 9. High-Risk Seams

These are the places most likely to matter when doing large changes:

1. `backend/app/api/v1/publish.py`
   Single highest-risk file. Current behavior, sanitization doctrine, and research assumptions all collide here.
2. `frontend/src/pages/Editor.tsx`
   State center of the UI. Any migration touches this file.
3. `frontend/src/components/preview/WechatPreview.tsx`
   Preview/editability contract lives here.
4. `frontend/src/components/panel/ActionPanel.tsx`
   Copy/publish behavior may already lag backend endpoint reality.
5. `backend/app/services/block_registry.py`
   Central extension seam for migration.
6. `backend/app/models/mbdoc.py`
   Migration contract and future API boundary.

## 10. Mismatches You Must Keep in Mind

These are the most important repo truths to preserve in future sessions:

1. The UI is legacy-article-first; the backend roadmap is block-first.
2. `MBDoc` exists, but the frontend does not run on it yet.
3. Research docs and handoff docs are rich, but they reflect multi-session work from earlier moments. They are useful, not authoritative over current code.
4. Some comments/tests/documentation describe a cleaner architecture than the code currently implements.
5. There are mojibake/encoding artifacts in several Chinese docs and comments when viewed in the current environment. Do not mistake encoding damage for conceptual damage.

## 11. Recommended Next-Step Heuristics

When making a large change, classify the task first:

- If it changes current production behavior, start from legacy article flow.
- If it advances the migration architecture, start from `MBDoc`, `BlockRegistry`, and `render_for_wechat`.
- If it touches both, explicitly write a compatibility boundary first.

Do not assume you can remove the legacy pipeline in one pass unless the frontend migration is part of the same change set.

## 12. Questions to Re-answer Before Major Refactors

Before doing any large iteration, answer these explicitly:

1. Are we extending the legacy article product or accelerating the MBDoc migration?
2. Does preview remain backend-processed, or should it become block-rendered directly?
3. Is `publish.py` being incrementally refactored, or replaced behind a new boundary?
4. Is `WechatTiptapEditor` in scope, or should it remain dormant?
5. Are docs/superpowers files historical reference, or still operational instructions for this phase?

If these five answers are unclear, implementation will drift.
