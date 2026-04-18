# MBEditor Unified Migration Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Migrate MBEditor toward an `MBDoc`-centered architecture while introducing an agent-first native `mbeditor` CLI and rewriting the project skill into a <=500 line CLI-first guide.

**Architecture:** Keep the current product shell and legacy `Article` routes alive, but move document truth and render truth toward `MBDoc`. Add a bridge layer in frontend and backend so preview/copy/publish converge before the UI is rewritten. Introduce a thin CLI that wraps current APIs first, then gradually make it the default agent entrypoint.

**Tech Stack:** FastAPI, Python, React 19, TypeScript, Vite, Docker Compose, WeChat API, Typer or Click, httpx, optional Rich, existing file-based storage.

---

## Rules

- Do not rewrite the UI shell first.
- Do not remove `/articles` or `/publish` early.
- Do not let preview move to `MBDoc` while copy/publish stay legacy.
- Do not dual-write `Article` and `MBDoc` as equal sources of truth.
- Do not expand `publish.py`; only shrink and isolate it.
- Skill must remain under 500 lines.
- CLI first version wraps existing APIs; it does not require backend architectural completion.

---

## Workstreams

There are four workstreams:

1. Backend render/document migration
2. Frontend bridge migration
3. CLI introduction
4. Skill/docs refactor

Parallel-safe:

- Backend render/document migration can run in parallel with CLI design and docs skeleton work.
- Frontend bridge extraction can start after backend boundaries and CLI contract are defined.
- Skill rewrite can start after CLI command surface is frozen.

Serialization points:

- Render truth must converge before frontend cutover.
- CLI command surface must be frozen before skill examples are finalized.
- Skill must not promise commands that do not exist.

---

### Task 1: Freeze Current Baseline

**Files:**
- Modify: `docs/architecture/PROJECT_MAP.md`
- Modify: `docs/architecture/SESSION_ONRAMP.md`
- Create: `docs/plans/2026-04-16-mbeditor-unified-migration-plan.md`
- Inspect: `data/articles/`
- Inspect: `backend/app/api/v1/publish.py`
- Inspect: `frontend/src/pages/Editor.tsx`
- Inspect: `frontend/src/components/preview/WechatPreview.tsx`
- Inspect: `frontend/src/components/panel/ActionPanel.tsx`

**Step 1: Freeze a representative legacy corpus**

Capture real examples from `data/articles/`:
- markdown-heavy article
- raw html article
- image-heavy article
- cover-image article
- complex CSS article

**Step 2: Record current behavior**

For each sample, record:
- `/publish/preview`
- copy-path HTML
- publish-path HTML or draft result

**Step 3: Commit documentation-only baseline capture**

```bash
git add docs/architecture docs/plans
git commit -m "docs: capture migration baseline and unified plan"
```

---

### Task 2: Define Backend Cut Points

**Files:**
- Modify: `backend/app/api/v1/publish.py`
- Create: `backend/app/services/document_projector.py`
- Create: `backend/app/services/publish_gateway.py`
- Modify: `backend/app/services/wechat_service.py`
- Modify: `backend/app/services/render_for_wechat.py`
- Modify: `backend/app/services/block_registry.py`
- Modify: `backend/app/api/v1/mbdoc.py`

**Step 1: Write failing tests for projector and publish boundary**

Targets:
- `Article -> MBDoc` projection for supported content
- publish path can accept already-rendered HTML plus metadata
- `render_for_wechat` remains single render entrypoint

**Step 2: Introduce `DocumentProjector`**

Responsibilities:
- convert legacy `Article` payload into bridge `MBDoc`
- later support reverse projection where needed

**Step 3: Introduce `PublishGateway`**

Responsibilities:
- accept final rendered HTML
- upload/resolve media
- derive cover or thumb
- call WeChat draft APIs

**Step 4: Shrink `publish.py`**

Allowed responsibilities after this task:
- route parsing
- compatibility glue
- call projector
- call render pipeline
- call publish gateway

**Step 5: Commit**

```bash
git add backend
git commit -m "refactor: isolate backend publish and document boundaries"
```

---

### Task 3: Implement Real Renderer Sequence

**Files:**
- Create: `backend/app/services/renderers/html_renderer.py`
- Create: `backend/app/services/renderers/markdown_renderer.py`
- Create: `backend/app/services/renderers/image_renderer.py`
- Create: `backend/app/services/renderers/svg_renderer.py`
- Create: `backend/app/services/renderers/raster_renderer.py`
- Modify: `backend/app/services/block_registry.py`
- Modify: `backend/tests/test_render_for_wechat.py`
- Modify: `backend/tests/test_mbdoc_api.py`
- Create: renderer-specific test files under `backend/tests/`

**Step 1: Replace `html` and `markdown` stubs**

Goal:
- no common text content should hit stub output

**Step 2: Replace `image` stub**

Goal:
- image behavior driven by `RenderContext.image_uploader`
- no regex-only final HTML mutation for image semantics

**Step 3: Replace `svg` stub**

Goal:
- validate supported SVG constraints
- preserve inline-safe SVG output

**Step 4: Replace `raster` stub**

Goal:
- formal raster block output path
- can stay minimal first version if backed by existing publish constraints

**Step 5: Register real renderers in `BlockRegistry.default()`**

**Step 6: Commit**

```bash
git add backend
git commit -m "feat: implement first complete MBDoc renderer set"
```

---

### Task 4: Extract Frontend Bridge Layer

**Files:**
- Create: `frontend/src/adapters/DocumentAdapter.ts`
- Create: `frontend/src/services/RenderService.ts`
- Create: `frontend/src/stores/editorSessionStore.ts` or `frontend/src/hooks/useEditorSession.ts`
- Modify: `frontend/src/pages/Editor.tsx`
- Modify: `frontend/src/components/preview/WechatPreview.tsx`
- Modify: `frontend/src/components/panel/ActionPanel.tsx`
- Modify: `frontend/src/components/ui/PublishModal.tsx`
- Modify: `frontend/src/types/index.ts`

**Step 1: Introduce bridge types**

Add types:
- `ArticleSnapshot`
- `MBDocSnapshot`
- `BridgeDoc`
- `RenderState`

**Step 2: Extract render and action logic out of `Editor.tsx`**

Move:
- preview request logic
- autosave orchestration
- processed html state
- publish/copy/export action preparation

**Step 3: Unify `ActionPanel` and `PublishModal` behavior**

Single source for:
- save-before-publish
- metadata selection
- publish request contract

**Step 4: Stop direct `Article` truth mutations**

`Editor.tsx` should update bridge/session state, not raw `Article` fields as the only source of truth.

**Step 5: Commit**

```bash
git add frontend
git commit -m "refactor: add frontend bridge document and render layer"
```

---

### Task 5: Converge Preview, Copy, and Publish

**Files:**
- Modify: `frontend/src/components/preview/WechatPreview.tsx`
- Modify: `frontend/src/services/RenderService.ts`
- Modify: `frontend/src/components/panel/ActionPanel.tsx`
- Modify: `frontend/src/components/ui/PublishModal.tsx`
- Modify: `backend/app/api/v1/publish.py`
- Modify: `backend/app/services/publish_gateway.py`

**Step 1: Make preview consume unified render result**

Preview should render output from one render pipeline, not a special-case representation.

**Step 2: Make copy consume the same processed render result**

No separate divergent transformation path.

**Step 3: Make publish consume the same processed render result**

Only media URL substitutions and WeChat transport details may vary.

**Step 4: Add tests proving parity**

Required checks:
- preview html vs copy html
- preview html vs publish html
- differences limited to image URL substitutions where expected

**Step 5: Commit**

```bash
git add frontend backend
git commit -m "refactor: unify preview copy and publish render outputs"
```

---

### Task 6: Design the Native `mbeditor` CLI

**Files:**
- Create: `docs/cli/CLI_OVERVIEW.md`
- Create: `docs/cli/COMMAND_REFERENCE.md`
- Create: `docs/cli/CLI_ANYTHING_NOTES.md`
- Create: `backend/app/cli/main.py`
- Create: `backend/app/cli/client.py`
- Create: `backend/app/cli/formatters.py`
- Create: `backend/app/cli/commands/article.py`
- Create: `backend/app/cli/commands/doc.py`
- Create: `backend/app/cli/commands/render.py`
- Create: `backend/app/cli/commands/publish.py`
- Create: `backend/app/cli/commands/image.py`
- Create: `backend/app/cli/commands/config.py`
- Modify: `backend/requirements.txt`
- Modify: `backend/requirements-dev.txt`

**Step 1: Freeze command surface**

Required command groups:
- `mbeditor article`
- `mbeditor doc`
- `mbeditor render`
- `mbeditor publish`
- `mbeditor image`
- `mbeditor config`

Global flags:
- `--base-url`
- `--json`
- `--timeout`
- `--quiet`

**Step 2: Choose CLI framework**

Prefer `Typer` if no repo constraint blocks it.
Fallback: `Click`.

**Step 3: Implement thin API client**

The first CLI version wraps current HTTP APIs only.

**Step 4: Implement first command tranche**

Required first tranche:
- `article list|get|create|update|delete`
- `render preview`
- `publish draft`

**Step 5: Implement second command tranche**

- `doc list|get|create|update|render`
- `image list|upload|delete`
- `config get|set|check`

**Step 6: Add `--json` stable output**

Every write command returns a predictable schema:
- `ok`
- `id`
- `message`
- `data`

**Step 7: Commit**

```bash
git add backend docs/cli
git commit -m "feat: add agent-first mbeditor cli"
```

---

### Task 7: Rewrite the MBEditor Skill to <=500 Lines

**Files:**
- Modify: `skill/mbeditor.skill.md`
- Create: `docs/agent/AGENT_WORKFLOWS.md`
- Create: `docs/agent/RENDER_DECISIONS.md`

**Step 1: Replace API-first guidance with CLI-first guidance**

The skill should default to:
- use `mbeditor` CLI first
- use HTTP API only as fallback or for debugging

**Step 2: Keep only high-signal content in the skill**

Must keep:
- trigger conditions
- current architecture boundary: legacy vs `MBDoc`
- HTML / SVG / Raster decision tree
- CLI-first examples
- links to deep docs

Must move out:
- long background and rationale
- large API tables
- repeated examples
- long migration commentary

**Step 3: Validate line budget**

Skill must remain under 500 lines.

**Step 4: Commit**

```bash
git add skill docs/agent
git commit -m "docs: rewrite mbeditor skill as cli-first short guide"
```

---

### Task 8: Adopt CLI-Anything Ideas Without Overcommitting

**Files:**
- Modify: `docs/cli/CLI_ANYTHING_NOTES.md`
- Modify: `docs/cli/CLI_OVERVIEW.md`
- Modify: `skill/mbeditor.skill.md`

**Step 1: Capture structural borrowings**

Borrow these ideas:
- command-first interface
- self-describing `--help`
- stable `--json` mode for agents
- short skill plus deep docs
- grouped commands by domain

**Step 2: Explicitly reject first-phase overreach**

Do not attempt in phase 1:
- full CLI-Anything 7-phase generation pipeline
- auto-generated harness packaging from MBEditor itself
- plugin marketplace integration
- CLI-Hub publishing

**Step 3: Commit**

```bash
git add docs/cli skill
git commit -m "docs: document CLI-Anything-inspired CLI constraints"
```

---

### Task 9: Add Agent-Facing Validation and Rollback Gates

**Files:**
- Modify: `backend/tests/`
- Modify: `frontend/src/utils/__tests__/`
- Create: `docs/agent/VALIDATION_GATES.md`
- Modify: `docs/architecture/PROJECT_MAP.md`

**Step 1: Add minimum gates**

Per phase require:
- baseline corpus checks
- renderer coverage checks
- preview/copy/publish parity checks
- CLI `--json` contract checks
- skill examples match existing commands

**Step 2: Add rollback notes**

Document:
- data directories to back up
- feature flags if introduced
- how to revert to legacy publish
- how to identify legacy-only vs bridge vs native-`MBDoc` documents

**Step 3: Commit**

```bash
git add backend frontend docs
git commit -m "test: add migration and cli validation gates"
```

---

### Task 10: Final Integration Review

**Files:**
- Review full repository changes

**Step 1: Run validation**

Required:
- backend tests
- frontend tests
- frontend build
- CLI smoke commands
- NAS canary verification if possible

**Step 2: Run final review**

Check:
- no command promised in skill is missing
- no preview/copy/publish divergence remains in migrated path
- no stub renderer is reachable for intended migrated flows

**Step 3: Commit final integration cleanup**

```bash
git add .
git commit -m "chore: finalize unified migration tranche"
```

---

## Recommended Parallel Execution

### Parallel Batch A

- Task 2: Backend cut points
- Task 6 Step 1-2: CLI surface design
- Task 7 Step 1-2: Skill short rewrite draft

### Parallel Batch B

- Task 3: Renderer sequence
- Task 4: Frontend bridge extraction
- Task 6 Step 3-6: CLI implementation
- Task 8: CLI-Anything notes

### Parallel Batch C

- Task 5: Render convergence
- Task 7 Step 3-4: Skill finalize
- Task 9: Validation gates

### Final Serial Batch

- Task 10: Integration review

---

## Immediate Recommendation

Start with:

1. Task 2
2. Task 6
3. Task 7

Reason:
- They unblock everything else.
- They can be split across backend, CLI, and docs/skill owners.
- They avoid premature UI rewrite.

---

Plan complete and saved to `docs/plans/2026-04-16-mbeditor-unified-migration-plan.md`.

Two execution options:

1. Subagent-Driven (this session) - I dispatch fresh subagent per task, review between tasks, and run the first batch in parallel-safe order.
2. Parallel Session (separate) - Open a new session with executing-plans and run the batches against the plan from a cleaner handoff.
