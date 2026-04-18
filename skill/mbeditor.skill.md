---
name: mbeditor
description: "MBEditor agent guide. Use for WeChat article authoring, rendering, preview, publish, image workflows, and architecture-aware changes."
user-invocable: true
metadata:
  openclaw:
    emoji: "📝"
    requires:
      bins: ["curl"]
---

# MBEditor Agent Skill

## Trigger

Use this skill when the user asks to:

- write, edit, render, preview, export, or publish a WeChat article
- build or modify MBEditor itself
- work on article/image/config APIs
- work on `MBDoc`, WeChat-safe rendering, or agent-driven document generation

## Current Truth

Hold these facts at the same time:

1. The shipped product still runs on legacy `Article`.
2. The target architecture is block-based `MBDoc`.
3. Preview, copy, and publish already depend on backend processing.
4. Migration is incomplete. Do not assume frontend or publish flow is fully `MBDoc`-native.

Read first:

1. `docs/architecture/SESSION_ONRAMP.md`
2. `docs/architecture/PROJECT_MAP.md`
3. `docs/agent/AGENT_WORKFLOWS.md`
4. `docs/agent/RENDER_DECISIONS.md`

## Lane Check

Before you act, classify the task:

- Lane A: current product behavior
  Work from legacy `Article`, `/articles`, and `/publish`.
- Lane B: migration architecture
  Work from `MBDoc`, block renderers, and render convergence.
- Lane C: bridge work
  Define explicit compatibility between `Article` and `MBDoc` before editing.

If you skip this step, changes drift across both systems.

## Entry Order

For code tasks, inspect in this order:

1. `backend/app/api/v1/publish.py`
2. `backend/app/api/v1/mbdoc.py`
3. `backend/app/services/render_for_wechat.py`
4. `backend/app/services/block_registry.py`
5. `frontend/src/pages/Editor.tsx`
6. `frontend/src/components/preview/WechatPreview.tsx`
7. `frontend/src/components/panel/ActionPanel.tsx`

## CLI-First Rule

MBEditor is moving to an agent-first `mbeditor` CLI.

Use this rule:

- If `mbeditor --help` works in the current checkout, prefer CLI.
- If `mbeditor` is not installed yet but backend deps are available, try `python -m app.cli --help` from `backend/`.
- If the CLI is not available yet, use the existing HTTP API.
- Do not promise CLI commands unless they exist in the current workspace.

CLI design docs:

- `docs/cli/CLI_OVERVIEW.md`
- `docs/cli/CLI_ANYTHING_NOTES.md`

## Current Interfaces

Current runtime surfaces:

- Web UI: `http://localhost:7073`
- API base: `http://localhost:7072/api/v1`

Current stable routes:

- `/articles`
- `/publish`
- `/images`
- `/wechat`
- `/mbdoc`

Current data reality:

- legacy articles are the live product path
- `MBDoc` renderer coverage now includes all built-in block types, but frontend authoring is still bridge-first and `raster` is still on its migration-phase fallback path

## Document Model Rule

Use the right source of truth for the job:

- editing current shipped behavior: treat `Article` as canonical
- implementing migration layers: `Article` may project into `MBDoc`
- future-native block work: `MBDoc` should become canonical

Do not dual-write `Article` and `MBDoc` as equal truths.

## Render Truth Rule

Never let these paths diverge without an explicit reason:

- preview
- copy/export
- publish/draft

Long-term rule: all three should consume one render result.

Short-term reality: the project is still converging there.

## HTML / SVG / Raster Decision

Choose the lowest layer that can express the result safely.

1. Use HTML first.
   Best for text, layout, lists, callouts, tables, simple cards, normal images.
2. Use SVG next.
   Best for vector illustration, decorative geometry, simple click-triggered visual changes.
3. Use raster only when HTML and SVG cannot represent the output.
   Best for effects that must be pixel-exact and are not meaningfully editable as WeChat-safe markup.

Prefer preserving selectable text over rasterizing it.

Detailed guidance:

- `docs/agent/RENDER_DECISIONS.md`

## WeChat Safety Rules

Assume WeChat is hostile to web-platform richness.

Default rules:

- inline styles beat external CSS
- do not rely on script execution
- do not rely on unsupported selectors or pseudo-element tricks
- do not assume complex browser layout survives unchanged
- validate against actual publish flow, not just local preview

If the user asks for complex visuals, reason through HTML -> SVG -> raster in that order.

## Current High-Risk Files

Treat these as architectural seams, not routine leaf files:

- `backend/app/api/v1/publish.py`
- `backend/app/services/wechat_service.py`
- `backend/app/services/block_registry.py`
- `frontend/src/pages/Editor.tsx`
- `frontend/src/components/preview/WechatPreview.tsx`
- `frontend/src/components/panel/ActionPanel.tsx`
- `frontend/src/components/ui/PublishModal.tsx`

## Working Rules

- Do not rewrite the UI shell first.
- Do not remove `/articles` or `/publish` early.
- Do not move preview to `MBDoc` while copy/publish stay legacy.
- Do not expand `publish.py`; shrink and isolate it.
- Do not assume research docs describe current runtime exactly.
- Keep agent instructions short here; move depth into docs.

## Current Fallback API Use

If CLI is not present, work through HTTP directly.

Common flow:

1. create or load article through `/articles`
2. update content and metadata
3. preview/process through `/publish/preview`
4. publish draft through `/publish/draft`
5. upload and manage images through `/images`
6. use `/mbdoc` only when task explicitly targets migration or block docs

## Recommended Agent Workflow

### For user content generation now

1. decide lane
2. decide render layer for each major section
3. create or update content through current product path
4. preview through backend processing
5. publish only after processed output looks correct

### For migration work

1. capture current behavior first
2. isolate boundary or adapter layer
3. keep preview/copy/publish parity
4. add or extend tests before removing compatibility

More:

- `docs/agent/AGENT_WORKFLOWS.md`

## CLI Transition Rule

During the CLI rollout:

- teach agents to prefer CLI when available
- keep API fallback documented
- avoid examples that claim a command exists before implementation lands
- keep human-readable and machine-readable output separate in docs

## When To Read More

Read architecture docs when:

- changing storage or source of truth
- changing preview/copy/publish behavior
- editing `publish.py`
- adding or modifying block renderers
- changing frontend editor state shape

Read research docs when:

- deciding HTML vs SVG vs raster
- deciding what WeChat actually preserves
- trying to make an interaction survive publish

## Escalation Triggers

Stop and clarify if:

- the task mixes legacy fixes and `MBDoc` migration with no stated boundary
- the user wants parity-critical publish changes without baseline validation
- the change would require deleting compatibility before renderer coverage exists

## Deliverable Style

When you complete work:

- state which lane you worked in
- state whether behavior is current-path, bridge, or `MBDoc`-native
- state what was validated and what was not
- cite the changed files

## Deep Docs

Use these instead of bloating this skill:

- `docs/architecture/SESSION_ONRAMP.md`
- `docs/architecture/PROJECT_MAP.md`
- `docs/plans/2026-04-16-mbeditor-unified-migration-plan.md`
- `docs/plans/2026-04-16-backend-mbdoc-migration.md`
- `docs/agent/AGENT_WORKFLOWS.md`
- `docs/agent/RENDER_DECISIONS.md`
- `docs/cli/CLI_OVERVIEW.md`
- `docs/cli/CLI_ANYTHING_NOTES.md`
