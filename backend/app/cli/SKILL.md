---
name: mbeditor-cli
description: Agent-first CLI for MBEditor. Author, render, publish WeChat articles.
trigger: mbeditor --help
---

# MBEditor CLI Skill

This is the machine-readable entry point to MBEditor. Prefer it over raw HTTP
calls when an agent needs to author, render, or publish WeChat content.

## First Moves

1. `mbeditor --help` - confirm the binary is on PATH.
2. `mbeditor info` - shows mode, data paths, resolved base URL.
3. `mbeditor skill` - re-prints this file.

If `mbeditor` is not installed, fall back to `python -m app.cli` from
`backend/`.

## Modes

- `--mode direct` (default) - operates on local files (`data/articles`,
  `data/mbdocs`, `data/images`, `data/config.json`). No FastAPI server
  required.
- `--mode http` - calls the running `/api/v1` backend via `--base-url`.

Override data location with `--data-dir PATH` or `MBEDITOR_DATA_DIR` env.

## Output Contract

Every command emits a stable envelope:

```json
{"ok": true, "action": "article.get", "message": "success", "data": {}}
```

- Add `--json` for machine output (default is also JSON for now).
- Add `--compact` with `--json` for single-line JSONL.
- `ok=false` + non-zero exit on errors.

## Command Map

| Group     | Direct mode      | HTTP mode  | Notes                                  |
|-----------|------------------|------------|----------------------------------------|
| `article` | yes              | yes        | File-backed CRUD.                      |
| `doc`     | yes              | yes        | MBDoc CRUD + render.                   |
| `image`   | yes              | yes        | Local library; no WeChat upload here.  |
| `render`  | yes              | yes        | `preview`, `article`, `doc`.           |
| `publish` | yes (needs creds)| yes        | Hits WeChat draft API; needs `config`. |
| `config`  | yes              | yes        | Reads/writes `data/config.json`.       |

## Common Recipes

Create a legacy article and render it:

```bash
mbeditor article create "Hello" markdown
mbeditor article update <id> --markdown "# Hi"
mbeditor render article <id> --json
```

Create an MBDoc from a JSON file, render preview, upload to WeChat:

```bash
mbeditor doc create sample.json
mbeditor doc render <id>                      # preview html
mbeditor doc render <id> --upload-images      # publish-ready html
```

Project a legacy article into an MBDoc:

```bash
mbeditor article project-to-doc <id> --persist --json
```

Publish a draft to WeChat:

```bash
mbeditor config set <appid> <secret>
mbeditor config check <appid> <secret>
mbeditor publish draft <id> "Author Name" "Short digest"
```

## Lane Rules

- Do not mix legacy Article work and MBDoc work without a projection step.
- `upload_images=False` is preview-safe; `upload_images=True` goes through
  the uploader and may hit network.
- SVG `<image>` with remote href is only allowed with `upload_images=False`.
- Raster blocks require an uploader at publish time; the renderer will
  raise rather than emit a `data:` URL into a WeChat draft.

## Escalation

If a command fails with `ok=false`:

1. Check `--mode` - direct mode needs the right `--data-dir`.
2. For HTTP mode, confirm `mbeditor info` shows the expected `base_url`.
3. For publish/config errors, re-run `config check` with the credentials.
