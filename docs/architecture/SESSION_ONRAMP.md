# MBEditor Session Onramp

Use this file when a new session needs to become productive quickly without re-reading the whole repository.

## 1. First 10 Minutes

Read these files in order:

1. `docs/architecture/SESSION_ONRAMP.md`
2. `docs/architecture/PROJECT_MAP.md`
3. `docs/superpowers/SESSION_HANDOFF.md`
4. `backend/app/api/v1/publish.py`
5. `backend/app/models/mbdoc.py`
6. `backend/app/services/block_registry.py`
7. `frontend/src/pages/Editor.tsx`
8. `frontend/src/components/preview/WechatPreview.tsx`
9. `frontend/src/components/panel/ActionPanel.tsx`

If the task is architectural, also read:

- `docs/research/wechat-wysiwyg-pipeline.md`
- `docs/research/wechat-svg-capability.md`
- `docs/research/html-to-svg-compilation.md`

## 2. Mental Model

Hold this model in your head:

- The shipped app still runs on legacy `Article`.
- The intended future architecture is `MBDoc`.
- Backend contains both worlds.
- Frontend mostly contains only the old world.
- Preview/copy/publish are already trying to centralize around backend processing.
- Migration is incomplete.

## 3. Where to Look for What

### Need current behavior?

Start here:

- `frontend/src/pages/Editor.tsx`
- `frontend/src/components/panel/ActionPanel.tsx`
- `backend/app/api/v1/publish.py`
- `backend/app/services/wechat_service.py`

### Need future architecture?

Start here:

- `backend/app/models/mbdoc.py`
- `backend/app/services/block_registry.py`
- `backend/app/services/render_for_wechat.py`
- `backend/app/api/v1/mbdoc.py`
- `docs/superpowers/plans/2026-04-11-mbeditor-wysiwyg-roadmap.md`

### Need evidence for a design decision?

Start here:

- `docs/research/wechat-wysiwyg-pipeline.md`
- `docs/research/wechat-svg-capability.md`
- `docs/research/html-to-svg-compilation.md`

## 4. Fast Truths

1. `publish.py` is the most overloaded file.
2. `Editor.tsx` is the most important frontend file.
3. `MBDoc` API exists, but frontend does not depend on it yet.
4. Some tests/docs/comments describe a cleaner state than the repo actually has.
5. Several docs have encoding damage in this environment; read through it, do not overreact to mojibake.

## 5. Current Validation Gaps

As of this session:

- backend dependencies are not installed locally, so `pytest` is unavailable
- frontend dependencies are not installed locally, so `vitest`, `tsc`, and `vite` are unavailable

That means source-of-truth understanding currently comes from code and docs inspection, not from a fresh local green run.

## 6. Decision Shortcut

Before coding, decide which lane you are in:

- Lane A: current product behavior
  Work from legacy `Article` flow.
- Lane B: migration architecture
  Work from `MBDoc` + `BlockRegistry`.
- Lane C: bridge work
  Define compatibility explicitly before editing.

If you skip this classification, changes will drift across both architectures and get harder to reason about.

## 7. What To Record After New Discoveries

If a future session discovers something durable, update one of these:

- `docs/architecture/PROJECT_MAP.md`
  for stable architecture truths
- `docs/architecture/SESSION_ONRAMP.md`
  for fast-entry guidance
- `docs/superpowers/SESSION_HANDOFF.md`
  for current execution status and staged work
