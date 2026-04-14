# MBEditor API 参考文档

> **环境变量（必读）：** 执行以下任何 curl 命令前，先设置环境变量。
> - `MBEDITOR_API_BASE` — API 服务地址，默认 `http://localhost:7072`
> - `MBEDITOR_WEB_BASE` — Web 编辑器地址，默认 `http://localhost:7073`

**快速设置：**
```bash
export MBEDITOR_API_BASE="${MBEDITOR_API_BASE:-http://localhost:7072}"
export MBEDITOR_WEB_BASE="${MBEDITOR_WEB_BASE:-http://localhost:7073}"
```

**远程部署设置示例：**
```bash
# 部署在云服务器 123.45.67.89 上
export MBEDITOR_API_BASE="http://123.45.67.89:7072"
export MBEDITOR_WEB_BASE="http://123.45.67.89:7073"
```

以下所有示例中的 `localhost:7072/7073` 均已替换为环境变量引用。

---

## 一、MBDoc API（Stage 1 起可用）

MBDoc 是 MBEditor 的新一代文档格式，是 Block 化的 JSON 结构。AI Agent 推荐直接产出 MBDoc JSON 并 POST，跳过"自己拼接 HTML 字符串"的陷阱。

### Schema

```json
{
  "id": "doc-20260411-001",
  "version": "1",
  "meta": {
    "title": "文章标题",
    "author": "作者名",
    "digest": "一句话摘要",
    "cover": "/images/cover.jpg"
  },
  "blocks": [
    { "id": "b1", "type": "heading", "level": 1, "text": "主标题" },
    { "id": "b2", "type": "paragraph", "text": "正文段落。" }
  ]
}
```

**id 约束：** `id`（文档 id 和 block id）必须匹配 `^[A-Za-z0-9_-]+$`（只允许字母、数字、连字符、下划线）。

### 当前可用的 block 类型（Stage 1）

| type | 状态 | 必填字段 |
|---|---|---|
| `heading` | ✅ 可用 | `level` (1-6), `text` |
| `paragraph` | ✅ 可用 | `text` |
| `markdown` | 🚧 stub（Stage 2 实装） | `source` |
| `html` | 🚧 stub（Stage 2 实装） | `source` |
| `image` | 🚧 stub（Stage 3 实装） | `src`（禁止 `javascript:` / `data:` 协议） |
| `svg` | 🚧 stub（Stage 4 实装） | `source`（必须含 `<svg>` 标签） |
| `raster` | 🚧 stub（Stage 5 实装） | `html`, `css` |

**stub 状态**：这些 block 会被渲染为醒目的黄色警告框，提醒尚未实装。Stage 2-5 会依次替换。

### MBDoc 端点

#### 1. 创建 MBDoc
```bash
curl -X POST "${MBEDITOR_API_BASE:-http://localhost:7072}/api/v1/mbdoc" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "doc-20260411-001",
    "version": "1",
    "meta": {"title": "Hello MBDoc", "author": "Anson"},
    "blocks": [
      {"id": "h1", "type": "heading", "level": 1, "text": "欢迎"},
      {"id": "p1", "type": "paragraph", "text": "这是第一个 MBDoc 文档。"}
    ]
  }'
```

#### 2. 获取 MBDoc
```bash
curl "${MBEDITOR_API_BASE:-http://localhost:7072}/api/v1/mbdoc/doc-20260411-001"
```

#### 3. 更新 MBDoc（完整替换）
```bash
curl -X PUT "${MBEDITOR_API_BASE:-http://localhost:7072}/api/v1/mbdoc/doc-20260411-001" \
  -H "Content-Type: application/json" \
  -d '{ ... 完整 MBDoc JSON ... }'
```

注意：PUT body 中的 `id` 必须与 URL 中的一致，否则返回 400。

#### 4. 列出所有 MBDoc
```bash
curl "${MBEDITOR_API_BASE:-http://localhost:7072}/api/v1/mbdoc"
```
返回 `{"code":0,"data":[{"id":"...","title":"..."}, ...]}`

#### 5. 渲染为 HTML（预览模式）
```bash
curl -X POST "${MBEDITOR_API_BASE:-http://localhost:7072}/api/v1/mbdoc/doc-20260411-001/render?upload_images=false"
```

#### 6. 渲染为 HTML（发布模式 — Stage 3 起真正上传图片）
```bash
curl -X POST "${MBEDITOR_API_BASE:-http://localhost:7072}/api/v1/mbdoc/doc-20260411-001/render?upload_images=true"
```

#### 7. 删除 MBDoc
```bash
curl -X DELETE "${MBEDITOR_API_BASE:-http://localhost:7072}/api/v1/mbdoc/doc-20260411-001"
```

### MBDoc WYSIWYG 不变量

`render_for_wechat` 是 MBEditor 预览/复制/推送草稿箱三条路径**唯一的真相来源**。调用两次同一个 MBDoc（一次 `upload_images=false`，一次 `upload_images=true`），产出的 HTML diff **必须只在 `<img src>` 属性上**。对纯文本文档（无 image block），两次调用产出完全一致。

### MBDoc Agent 工作流示例

```bash
cat > /tmp/doc.json <<'EOF'
{
  "id": "demo-001",
  "version": "1",
  "meta": {"title": "AI 生成的文章", "author": "Claude"},
  "blocks": [
    {"id": "h1", "type": "heading", "level": 1, "text": "AI 如何改变写作"},
    {"id": "p1", "type": "paragraph", "text": "人工智能正在重塑内容生产方式..."},
    {"id": "h2", "type": "heading", "level": 2, "text": "关键变化"},
    {"id": "p2", "type": "paragraph", "text": "效率、质量、创意都被重新定义。"}
  ]
}
EOF

curl -X POST "${MBEDITOR_API_BASE:-http://localhost:7072}/api/v1/mbdoc" \
  -H "Content-Type: application/json" -d @/tmp/doc.json

curl -sX POST "${MBEDITOR_API_BASE:-http://localhost:7072}/api/v1/mbdoc/demo-001/render" | jq -r .data.html
```

### Stage 1 限制（已知）

- `markdown` / `html` / `image` / `svg` / `raster` 5 种 block 都是 stub（渲染为黄色警告框）
- `render?upload_images=true` 还没有真正的图片上传逻辑（Stage 3 实装）
- 前端 Editor 页面仍在 legacy `/articles` 界面；MBDoc 目前**只能通过 API 操作**
- `/articles` 和 `/mbdoc` 是两套独立存储，无数据迁移工具
- MBDocStorage 无并发锁（单用户单机假设），两个并发 PUT 有竞争

---

## 二、Articles API（Legacy，Stage 6 下线）

### 1. 创建文章
```bash
curl -X POST "${MBEDITOR_API_BASE:-http://localhost:7072}/api/v1/articles" \
  -H "Content-Type: application/json" \
  -d '{"title":"文章标题","mode":"html"}'
```
- **mode**: `html` 或 `markdown`
- 返回文章对象，包含 `id` 字段（后续操作都用这个 id）

### 2. 列出所有文章
```bash
curl "${MBEDITOR_API_BASE:-http://localhost:7072}/api/v1/articles"
```

### 3. 获取文章详情
```bash
curl "${MBEDITOR_API_BASE:-http://localhost:7072}/api/v1/articles/{article_id}"
```

### 4. 更新文章内容
```bash
curl -X PUT "${MBEDITOR_API_BASE:-http://localhost:7072}/api/v1/articles/{article_id}" \
  -H "Content-Type: application/json" \
  -d '{"html":"<h1>标题</h1><p>正文内容</p>","css":"h1{color:#333;font-size:24px;}"}'
```
可更新字段：`title`, `mode`, `html`, `css`, `js`, `markdown`, `cover`, `author`, `digest`

### 5. 删除文章
```bash
curl -X DELETE "${MBEDITOR_API_BASE:-http://localhost:7072}/api/v1/articles/{article_id}"
```

### Markdown 模式（Legacy API）

更新文章时设置 `"mode":"markdown"`，然后写入 `"markdown"` 字段：
```bash
curl -X PUT "${MBEDITOR_API_BASE:-http://localhost:7072}/api/v1/articles/{id}" \
  -H "Content-Type: application/json" \
  -d '{"mode":"markdown","markdown":"# 标题\n\n正文 **加粗** 内容"}'
```
Web 编辑器会自动用主题渲染为带 inline style 的 HTML。

**限制：** Markdown 模式只覆盖 HTML 层（段落、标题、列表、引用、代码、表格、图片）。如果你需要 SVG 或 Raster 效果，要么：
- 在 Markdown 里直接嵌入 `<svg>` 标签（marked 会原样透传）
- 切换到 `mode: "html"` 手写完整结构
- 等 Stage 1 的 MBDoc API 上线后用 block 化格式，混合 markdown + svg + raster

### 什么时候用哪套 API？

| 场景 | 推荐 |
|---|---|
| AI Agent 通过 CLI 生产文章（Stage 1+） | `/mbdoc` |
| 程序员手写 HTML 直接推送草稿箱（现在） | `/articles` |
| 运营者在 Web 编辑器里操作（现在） | `/articles` |
| Stage 6 起 | 全部 `/mbdoc`，`/articles` 下线 |

---

## 三、图片管理 API

### 1. 上传图片
```bash
curl -X POST "${MBEDITOR_API_BASE:-http://localhost:7072}/api/v1/images/upload" \
  -F "file=@/path/to/image.jpg"
```
- 返回：`{"data":{"id":"md5hash","path":"2026/04/04/md5hash.jpg",...}}`
- 在文章 HTML 中引用：`<img src="/images/2026/04/04/md5hash.jpg" style="max-width:100%;" />`
- 同一张图自动 MD5 去重

### 2. 列出所有图片
```bash
curl "${MBEDITOR_API_BASE:-http://localhost:7072}/api/v1/images"
```

### 3. 删除图片
```bash
curl -X DELETE "${MBEDITOR_API_BASE:-http://localhost:7072}/api/v1/images/{image_id}"
```

---

## 四、发布 API

### 1. 获取处理后的 HTML（供查看）
```bash
curl "${MBEDITOR_API_BASE:-http://localhost:7072}/api/v1/publish/html/{article_id}"
```
返回原始 HTML + CSS。

### 2. 处理文章图片（替换为微信 CDN URL）
```bash
curl -X POST "${MBEDITOR_API_BASE:-http://localhost:7072}/api/v1/publish/process" \
  -H "Content-Type: application/json" \
  -d '{"article_id":"xxx"}'
```
- 将文章中所有本地图片上传到微信 CDN 并替换 URL
- 需要先配置微信 AppID/AppSecret

### 3. 推送到微信草稿箱
```bash
curl -X POST "${MBEDITOR_API_BASE:-http://localhost:7072}/api/v1/publish/draft" \
  -H "Content-Type: application/json" \
  -d '{"article_id":"xxx","author":"作者名","digest":"文章摘要"}'
```
- 自动处理图片上传到微信 CDN + URL 替换
- 自动上传封面图
- 需要先配置微信 API

---

## 五、配置 API

### 1. 查看配置状态
```bash
curl "${MBEDITOR_API_BASE:-http://localhost:7072}/api/v1/config"
```

### 2. 设置微信 AppID/AppSecret
```bash
curl -X PUT "${MBEDITOR_API_BASE:-http://localhost:7072}/api/v1/config" \
  -H "Content-Type: application/json" \
  -d '{"appid":"wx...","appsecret":"..."}'
```

---

## 六、完整工作流示例

### Agent 写文章并发布（HTML 模式）

```bash
# 0. 设置环境变量（首次使用或远程部署时）
export MBEDITOR_API_BASE="${MBEDITOR_API_BASE:-http://localhost:7072}"
export MBEDITOR_WEB_BASE="${MBEDITOR_WEB_BASE:-http://localhost:7073}"

# 1. 创建文章
curl -s -X POST "${MBEDITOR_API_BASE}/api/v1/articles" \
  -H "Content-Type: application/json" \
  -d '{"title":"AI 如何改变我们的生活","mode":"html"}' | jq .data.id
# 返回: "abc123def456"

# 2. 写入内容（全 inline style，无 class，无 <style> 块）
curl -X PUT "${MBEDITOR_API_BASE}/api/v1/articles/abc123def456" \
  -H "Content-Type: application/json" \
  -d '{
    "html": "<section style=\"padding:20px 24px;font-family:-apple-system,BlinkMacSystemFont,\\\"PingFang SC\\\",sans-serif;\"><h1 style=\"font-size:26px;font-weight:700;line-height:1.4;color:#222;text-align:center;margin:0 0 20px;\">AI 如何改变我们的生活</h1><p style=\"font-size:16px;line-height:1.8;color:#333;margin:12px 0;\">人工智能正在深刻地改变着我们的日常生活...</p></section>",
    "css": "",
    "author": "Anson",
    "digest": "探讨 AI 技术对日常生活的影响"
  }'

# 3. 上传封面图（会自动去重）
curl -X POST "${MBEDITOR_API_BASE}/api/v1/images/upload" -F "file=@cover.jpg"
# 返回 path，然后更新文章的 cover 字段

# 4. 推送到草稿箱（会自动上传正文图片到微信 CDN）
curl -X POST "${MBEDITOR_API_BASE}/api/v1/publish/draft" \
  -H "Content-Type: application/json" \
  -d '{"article_id":"abc123def456","author":"Anson"}'
```

### 查看预览

```
请打开 ${MBEDITOR_WEB_BASE:-http://localhost:7073}/editor/{article_id} 查看预览效果
```

---

## 七、Publish Pipeline 已知陷阱（v4.0 记录）

下面是 2026-04-12 校准 MB 科技测试公众号时踩过的坑。遇到"内容发不出去"、"高度爆炸"、"按钮不见"的症状先查这里。

### 陷阱 1：`.reveal` / scroll-reveal 让内容隐形

**症状**：push 到草稿后，hero / footer 能看到，中间内容（段落、卡片、列表）**全部空白**。

**机制**：源 HTML 有这种 CSS：
```css
.reveal{opacity:0;transform:translateY(32px);transition:...;}
.reveal.visible{opacity:1;transform:translateY(0);}
```
和一段 JS `IntersectionObserver` 在滚到视口时加 `.visible`。微信禁 JS，`.visible` 永远不会加，所有 `.reveal` 元素保持 `opacity:0` 永远不可见。

**自动修复**：publish 流水线把 `opacity:0` 改写成 `opacity:1`、`transform:translateY(...)` 改写成 `transform:none`，strip 所有 `transition*` / `animation*`。

**Agent 预防**：不要设计依赖 scroll-reveal / fade-in / slide-up 的视觉效果。静态内容就静态内容，动画只在 SVG 层用 SMIL `begin="click"`。

### 陷阱 2：`position:absolute` 装饰撑爆父容器

**症状**：hero 区域高度从 366 px 暴涨到 1100+ px，floating orbs / 角标 / overlay 按钮跑到容器的正中间挤压正文。

**机制**：微信 MP 后端 ingest 时**把所有 `position` 属性全删**（实测：push 7 个 `position:absolute` + 15 个 `position:relative`，draft 里 0 个）。装饰元素（例如 `<div class="orb">` 220×220 浮动圆球）失去 absolute 后变 static block，占据 220 px 纵向空间。3 个 orb 瞬间加了 660 px。

**自动修复**：publish 流水线检测 `position:absolute|fixed` → 替换 `display:none` + strip `top/right/bottom/left/inset`。装饰性 absolute 元素直接消失。

**Agent 预防**：
- 不要用 absolute 定位做装饰（orb、角标、overlay badge）
- 需要装饰图形，用 `background-image` / `background: linear-gradient(...)` / `background-size`
- 需要角标用 `display:inline-block` + `float:right` 或 flex container 的 `justify-content: space-between`
- **特殊后果**：publish 流水线会把你的装饰元素完全隐藏。Agent 生成 HTML 时就不要指望 absolute 能工作。

### 陷阱 3：`<a>` 标签全部被微信 strip

**症状**：写在正文里的下载按钮 / 链接按钮视觉上消失；原位是其他内容直接上挤。

**机制**：微信只允许以下三类链接出现在正文：
1. 小程序跳转
2. 同公众号历史文章
3. 底部"阅读原文"（每篇文章只能一个）

任何 `<a href="https://外部">` 都会被 **ingest 时整个元素删除**，连内部文字一起没。

**自动修复**：publish 流水线把 `<a ...>text</a>` 转成 `<section ...>text</section>`，丢弃 `href`/`target`/`rel`/`download` 但保留 inline style（按钮视觉保留）。同时 `_publish_draft_sync` 会抽取原始 HTML 中第一个外部 `<a href="https://...">` 的 URL 塞进草稿的 `content_source_url` 字段，变成公众号"阅读原文"按钮 — 这是读者**唯一能点击的外部入口**。

**Agent 预防**：
- 下载 / 注册 / 购买按钮写成带 inline 样式的 `<a href="外部 URL">按钮文字</a>`，publish 流水线会帮你保留视觉 + 绑定阅读原文
- **每篇文章最多一个外部 URL**（`content_source_url` 只能设一个）。如果写了多个 `<a href>`，第一个会被抽取，其余失去点击
- 需要引导多个外部地址时，文案写"访问 www.xxx.com"让读者手抄/复制，不要依赖 `<a>` 点击

### 陷阱 4：`display:grid` / `display:flex` 能用，以前不能用

2026-04 前的 skill 文档声称 "display:grid → 微信不支持，会退化错乱"。**这条已过时**。实测（2026-04-12）：

- 微信 MP 草稿编辑视图（ProseMirror contenteditable）基于 Chromium 渲染，**完整支持 grid / flex**
- 只要把 grid rule 写成 inline `style="display:grid; grid-template-columns:1fr 1fr; gap:12px"`，grid 激活正常
- publish 流水线（premailer + cssutils）正确 inline grid properties

**Agent 可放心用**：多列卡片、数据仪表盘、兼容品牌网格等。但注意 grid item 的 `position:absolute` 子元素（陷阱 2）和 hover 样式（静态不生效）。

### 陷阱 5：host-port shadowing（部署侧）

**症状**：docker compose up 后，镜像内 `config.py` 显示 v4.0.0，但 curl API 返回旧版本号。

**机制**：Windows 主机上有另一个 Python 进程（例如之前手工 `uvicorn` 开的开发后端，或者别的项目）在监听相同端口（例如 7072）。docker 的 vpnkit port proxy 尝试 bind 失败，请求被僵尸 listener 截获。

**排查**：
```powershell
Get-NetTCPConnection -LocalPort 7072 -State Listen | ForEach-Object {
    Get-Process -Id $_.OwningProcess | Select-Object Id,ProcessName,StartTime
}
```
如果看到非 `com.docker.backend` 的进程，kill 它再 `docker compose down && docker compose up -d`。

### 陷阱 6：uvicorn 不用 `--reload` 时缓存旧字节码

**症状**：改了 `publish.py` 后 API 表现仍然是旧逻辑；重启 backend 立刻好。

**机制**：生产用 `uvicorn app.main:app` 启动，进程加载后**不会 reload**。docker 部署下重启容器会正常拉新代码；本地开发直接跑 uvicorn 改完代码要手工 kill 重启。

**开发建议**：本地开发一律用 `uvicorn app.main:app --reload --port 8001`。写自动化测试时用 `scripts/test_publish_direct.py` 绕开 API，直接 import `_process_for_wechat` 避免字节码陷阱。

### 校准工具（踩坑后必备）

- `backend/tests/visual/dump_wechat_computed_styles.py` — 推基线 doc 到草稿并 dump 编辑器视图的完整 computed style 到 JSON。校准视觉一致度的 ground truth。
- `scripts/test_publish_html.py <html>` — 一条龙：创建 article → 上传 HTML → preview → draft → screenshot。
- `scripts/compare_source_vs_draft.py <html> <media_id>` — source HTML ↔ draft 草稿 side-by-side 四象限对比。
- `backend/tests/visual/_artifacts/wechat_computed_styles.json` — 最近一次 dump 的参考数据（letter-spacing 0.578px、padding 0 4px、font-family 完整栈等）。

### 视觉还原度参考（printmaster_wechat_animated.html 基线）

| 阶段 | Draft 高度 | vs source 4564 |
|---|---|---|
| 未修复（旧 backend） | 7496 | +64.24% |
| 修复 reveal hide | 5212 | +14.20% |
| 修复 absolute→display:none | 4519 | -0.99% |
| 修复 `<a>`→`<section>` | **4547** | **-0.37%** |

结构还原度 100%，几何还原度 99.6%。剩余的 sub-pixel 字符漂移来自 WeChat 容器的 `letter-spacing: 0.578px`，无法通过 publish 流程消除（需要改源文本）。
