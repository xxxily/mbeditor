---
name: mbeditor
description: "MBEditor — 首款 AI Agent 原生的微信公众号编辑器。帮助 Agent 设计任意风格的公众号文章，自动保证在微信后台 100% 还原呈现。当用户提到公众号、微信文章、推文、草稿箱、或要求写/排版/设计/发布公众号内容时触发。"
user-invocable: true
metadata:
  openclaw:
    emoji: "📝"
    requires:
      bins: ["curl"]
---

# MBEditor — AI Agent 原生的公众号编辑器

**API 服务**: `${MBEDITOR_API_BASE:-http://localhost:7072}/api/v1`
**Web 编辑器**: `${MBEDITOR_WEB_BASE:-http://localhost:7073}`

> **环境变量（Agent 操作 API 前必读）：** 默认假设 MBEditor 通过 Docker 部署在本地。如果部署在其他服务器，需要设置环境变量。
>
> **读取优先级（从高到低）：**
> | 优先级 | 来源 | 说明 |
> |---|---|---|
> | 1 | `source .env` | 项目根目录的 `.env` 文件（参照 `.env.example`） |
> | 2 | Shell 已设置 | Docker/CI 环境中已设置的同名变量 |
> | 3 | 默认值 | `http://localhost:7072`（API）/ `http://localhost:7073`（Web） |
>
> **推荐做法：操作前先在 `.env` 文件中配置：**
> ```bash
> export MBEDITOR_API_BASE="http://服务器地址:7072"
> export MBEDITOR_WEB_BASE="http://服务器地址:7073"
> ```

---

## 🎯 核心使命（先读这一段）

MBEditor 给 Agent 两个承诺：

1. **最大设计自由** — 你可以用任何 HTML/CSS/SVG/栅格化手段实现你想要的视觉效果，不需要在创作时被微信的兼容性限制束缚思路。
2. **100% 微信还原** — 你设计的页面会**原样**呈现在微信公众号后台和读者的手机上，不会"预览好看但发布后崩掉"。

**这两件事看起来矛盾，因为微信正文支持的 HTML/CSS 极窄。** MBEditor 的做法是让你把设计**按复杂度分层**：能用微信原生 HTML 表达的就用 HTML，表达不了的用 SVG，SVG 也表达不了的用 Playwright 栅格化成 PNG。整个过程对你透明——你只管设计。

---

## 🧭 设计决策树（Agent 必读）

当用户要求某个视觉效果时，先问自己三个问题：

### 问题 1：这个效果能用"纯文字/图片/简单样式"表达吗？

**能 → 走 HTML 层。** 包括：标题、段落、列表、引用、代码块、表格、普通图片、边框、圆角、背景色、字体样式、颜色渐变（linear-gradient）、flexbox 简单布局（水平/垂直排列）。

**⚠️ 以下写法在 HTML 层会 100% 失效，必须改层：**
- `class` + 外部 `<style>` → 微信会剥光 style 标签
- `<script>` 任何形式 → 微信会删除
- `<input>` / `<label>` checkbox hack → 微信会删除
- ~~`display: grid` → 微信不支持，会退化错乱~~ **已过时**：v4.0 起 publish 流水线正确保留 grid，微信编辑视图完整支持（见 api-reference.md § 七）
- `position: fixed / absolute` → v4.0 起 publish 检测到会转 `display:none`（微信后端全删 `position` 属性），装饰元素**彻底消失**。不要依赖这个做装饰
- CSS `@keyframes` / `animation` → 依赖 style 标签，会失效
- `:hover` / `:active` / `::before` / `::after` → 不生效

**正确的 HTML 层写法：所有样式写 inline，不使用任何 class / 外部 CSS。**

**MBEditor publish 流水线自动处理对照表（v4.0+）：**

| 原始写法 | 自动处理 | 结果 |
|---|---|---|
| `display:grid` + `grid-template-columns` | **保留** | ✅ 激活正常 |
| `display:flex` | **保留** | ✅ 激活正常 |
| `position:absolute` 装饰元素 | 转 `display:none` | ⚠️ 元素不显示|
| `<a href="https://外部">` | 转 `<section>` 保留按钮样式 | ⚠️ 失去点击，URL 进"阅读原文" |
| `opacity:0` + scroll-reveal | `opacity:0` → `1` | ✅ 内容可见 |
| `transform:translateY(...)` | 转 `transform:none` | ✅ 位置正确 |
| `transition` / `animation` 属性 | 全 strip | ⚠️ 无动画|
| `@keyframes` / `@media` / `:hover` / `::before` | 全 strip | ⚠️ 规则被丢 |
| `class` 属性 | 全删 | ⚠️ 写 inline |

**Agent 设计建议**：
- **放心用 grid / flex** 做多列布局，publish 流水线保留完整
- **不要依赖 `position:absolute` 做装饰**（orb、badge overlay、角标等）——会被 hidden，改用 background-image 或 inline flex
- **下载 / 外链按钮**放末尾当 `<a>`，它会被转 section 保留视觉，真实外链通过公众号"阅读原文"访问
- **不要依赖 scroll-reveal / opacity:0 等 JS 动画** 做"首次加载才显示"
- **动画只用 SVG SMIL `begin="click"`**，不要用 CSS transition/animation（会被 strip）

### 问题 2：这个效果是"点击触发、图形装饰、矢量图标、简单动画"吗？

**是 → 走 SVG 层。** 微信允许 `<svg>` 正文嵌入，支持一个**有限**的 SMIL 动画集合：
- `<animate>` + `begin="click"` / `"touchstart"` 可做点击触发的透明度/位移动画
- `<animateTransform>` 可做旋转/缩放/平移
- `<rect> <circle> <path> <text>` 可画任意几何图形和矢量文字
- `<linearGradient>` 可做渐变填充

**SVG 层硬禁令：**
- ❌ 绝对不要用 `id="..."` 属性（微信全过滤，会导致 `use`、`clipPath` 引用断裂）
- ❌ 绝对不要用 `<script>` / `onclick=` / `onload=` 等事件属性
- ❌ 不要在 svg 内嵌 `<style>` 标签（会被剥离）
- ❌ 不要用 `<a>` 超链接

SVG 的 CSS 必须直接写在元素的 `style="..."` 属性里，或作为 `fill=""` `stroke=""` 这类 SVG 原生属性。

### 问题 3：既不能 HTML 表达、也不能 SVG 表达？

**走 Raster 层（栅格化）。** 适用场景：
- 3D 翻转 / perspective
- 复杂的 CSS 动画背景
- 任何你觉得"微信肯定不支持"的花哨效果
- （~~display:grid~~ 在 v4.0 起不再需要 raster）

Raster 层把你的 HTML+CSS 送到 Playwright 服务端用 headless Chromium 截图成 PNG，上传到微信 CDN，content 里最终只有一个 `<img>` 标签。**代价：** PNG 里的文字用户**不能选中复制**，也不能点击交互。但视觉上 100% 像素级还原。

### 层级选择优先级（决策树速查）

```
用户要求 "xxx 效果"
    │
    ▼
能用 inline style HTML 表达？  ─── 是 ──▶ HTML 层（最优，文字可选）
    │
    否
    ▼
能用纯 SVG（无 id/script）表达？  ─── 是 ──▶ SVG 层（矢量清晰）
    │
    否
    ▼
走 Raster 层（栅格化兜底，牺牲可选文字换取视觉还原）
```

**核心原则：能用低层就用低层，不要过度滥用 Raster。** 栅格化每块增加 2-3 秒发布时间，且 PNG 无法被搜索引擎索引。但当且仅当低层无法表达时，raster 是你的免死金牌。

---

## ⚠️ 重要变更公告（2026-04）

**Agent 需要知道以下正在发生的架构重构：**

1. **"内置 6 种交互组件" 正在被移除。** 旧版宣传的"展开收起 / 前后对比 / 翻牌卡片 / 滑动轮播 / 渐显文字 / 长按揭秘"本质是 HTML checkbox hack，已被调研证明在微信正文中全部被剥光。**这些组件在 Stage 0 已下线**，不要再在代码里引用它们。如果用户要做点击交互，用 SVG + SMIL `begin="click"`；如果要做复杂卡片翻转，用 Raster 层。

2. **新的 MBDoc block 化 API 即将到来（Stage 1）。** 格式是 JSON block 列表，每个 block 是 `heading` / `paragraph` / `markdown` / `html` / `image` / `svg` / `raster` 之一。Agent 通过 POST JSON 即可完成文章生产，无需手动拼接 HTML 字符串。**Stage 1 上线前，继续用 `/articles` API。**

3. **统一渲染管线：** 未来 `render → 一键复制 → 推送草稿箱` 三条路径会共享同一个 `render_for_wechat` 函数，保证预览和发布**字节级一致**（除图片 src 外）。

**执行中的 roadmap：** `docs/superpowers/plans/2026-04-11-mbeditor-wysiwyg-roadmap.md`

---

## MBDoc 文档模型速览（Stage 1 起可用）

MBDoc 是 MBEditor 的**新一代文档格式**，是 Block 化的 JSON 结构。AI Agent 推荐直接产出 MBDoc JSON 并 POST，跳过"自己拼接 HTML 字符串"的陷阱。

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

### 当前可用的 block 类型

| type | 状态 |
|---|---|
| `heading` | ✅ 可用 |
| `paragraph` | ✅ 可用 |
| `markdown` / `html` | 🚧 stub（Stage 2） |
| `image` | 🚧 stub（Stage 3） |
| `svg` | 🚧 stub（Stage 4） |
| `raster` | 🚧 stub（Stage 5） |

**stub 状态**：这些 block 会被渲染为醒目的黄色警告框，提醒尚未实装。

### 完整 API 参考

MBDoc 的 CRUD 端点、渲染 API、投影端点、以及 Articles/图片/发布/配置 的完整 API 文档和 curl 示例，请查阅 **[api-reference.md](api-reference.md)** 文件。该文件包含：
- MBDoc 7 个基础端点（创建/获取/更新/列表/渲染/删除）
- MBDoc 4 个投影端点（Legacy Article → MBDoc 投影/渲染/发布）
- Articles 端点（Legacy，Stage 6 下线）
- 图片上传/列表/删除
- 发布到微信草稿箱（含一键复制处理）
- 微信 AppID/AppSecret 配置 + 凭证测试
- 版本查询与更新检查
- 完整工作流 curl 示例
- Publish Pipeline 已知陷阱和排查指南

> **只有当你需要执行 API 操作（创建文章、上传图片、推送草稿箱等）时，才去查阅 api-reference.md。** 本文档专注于设计原则和写作规范。

---

## 工作流

用户可以直接说"帮我写一篇公众号文章"、"把这段内容发到公众号"、"上传封面图"等自然语言，你来调用对应 API。

### 典型流程：写文章 → 发布

1. **分层决策** — 先根据上文的"设计决策树"判断每个视觉块应该走 HTML / SVG / Raster 哪一层
2. **创建文章** — `POST /api/v1/articles`（或 `POST /api/v1/mbdoc`）获取 `article_id`
3. **生成内容** — 按分层决策组装 HTML/CSS 或 Markdown 源码（严格遵守 HTML 层写作规范）
4. **上传图片** — 通过 `/api/v1/images/upload` 上传到图床（自动 MD5 去重）
5. **推送草稿箱** — `POST /api/v1/publish/draft` 一键发布，或提示用户去 Web 编辑器复制富文本

具体的 API 端点、请求参数、curl 示例 → 查看 **[api-reference.md](api-reference.md)**。

---

## 写作指南

### HTML 层写作规范（Agent 请严格遵守）

> 这是针对**HTML 层**的规范。如果你要写的是 SVG 或 Raster block，规则不同——分别参照上文的决策树。

**必须遵守（违反就会出错）：**

1. **全部用 inline style**。禁止 `class="..."` + 外部 `<style>` 块。CSS 必须直接写在元素的 `style=""` 属性里。
2. **用 `<section>` 代替 `<div>`**。微信 WebView 对 section 支持更好，是 Xiumi/135 的业界惯例。
3. **用 `<p>` 写段落**，不要用 `<section><br></section>`。
4. **图片必须是微信 CDN URL（mmbiz.qpic.cn）或走 MBEditor 图片上传管线。** 外链图片会被微信过滤。你不需要手动上传——通过 `/api/v1/images/upload` 上传后插入 `<img src="/images/...">`，推送草稿箱时 MBEditor 会自动替换为 mmbiz URL。
5. **图片加 `style="max-width:100%;display:block;"`** 避免在手机上溢出。
6. **内容宽度 ≤ 578px**（微信文章有效宽度）。
7. **`<script>`、`<style>`、`<link>` 不能出现在 content 里**——即便写了也会被后端清洗掉，不如从一开始就不写。

**建议（效果更好）：**

- 字号用 `px` 不用 `rem/em`（微信 WebView 对相对单位不稳定）
- 颜色用 16 进制 `#333333`，不用 `rgb()` 或 CSS 变量
- 字体栈建议：`-apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif`
- 行高 `1.8` 阅读最舒适
- 正文字号 `16px`，一级标题 `26px`，二级标题 `22px`，三级标题 `19px`

**v4.0 起可以用（publish 流水线帮你处理）：**

- ✅ `display: grid` + `grid-template-columns` + `gap` — 正确保留激活
- ✅ `display: flex` + 复杂嵌套 — 正确保留
- ✅ 原 `opacity:0` / `transform:translate` 动画初态 — 自动改为可见状态

**仍禁止（写了会出视觉问题）：**

- ⚠️ `position: fixed / absolute / sticky` — v4.0 publish 会转 `display:none`，装饰元素**彻底消失**。不要用这个做装饰（orb / badge overlay / 角标），改用 background-image / linear-gradient / flex align
- ❌ `transform: rotate() / scale()`（非 translate） — 不稳定
- ❌ `@keyframes`、`animation:` — v4.0 publish 直接 strip，没有动画效果
- ❌ `transition:` — 同上 strip
- ❌ `:hover`、`:active`、`::before`、`::after`（伪类/伪元素不生效）
- ❌ `backdrop-filter`、`mix-blend-mode`（WebView 不支持）
- ❌ 任何引用 `class` 的选择器（class 属性会被删）
- ⚠️ `<a href="外部 URL">` — v4.0 publish 会转 `<section>` 保留视觉但失去点击。真正要外链就只有一个"阅读原文"位（`content_source_url`）

**如果用户的设计要求必须用以上禁止写法，你应该把这一块改投到 SVG 层或 Raster 层**，而不是强行写 HTML。

### 交互组件（Stage 0 起已下线）

> ⚠️ **不要使用"展开收起 / 前后对比 / 翻牌卡片 / 滑动轮播 / 渐显文字 / 长按揭秘"这 6 种旧组件。** 它们基于 `<input type=checkbox>` + `<label>` + `<style>` + `:checked` 的 HTML hack，微信正文会把 `<input>` / `<label>` / `<style>` / `class` 四样**全部剥光**，用户看到的是崩溃的静态布局。

**想实现交互效果的正确做法：**

| 想要的效果 | 正确的层级 | 实现方式 |
|---|---|---|
| 点击展开 / 收起 | SVG 层 | `<animate begin="click" attributeName="opacity" from="0" to="1">` |
| 点击切换图片（前后对比） | SVG 层 | 两个 `<image>` + 点击时 SMIL 切换 opacity |
| 翻牌 / 卡片翻转 | Raster 层 | 栅格化整个卡片，丢失翻转动画但保留视觉 |
| 图片轮播 | SVG 层 | 三个 `<image>` + `<animate>` 轮流切换 |
| 文字渐入 | SVG 层 | `<text>` + `<animate attributeName="opacity" begin="0s" dur="1s">` |
| 长按显示 | 放弃 | 微信 WebView 没有稳定的 long-press 模型 |

**通用原则：** 交互 = SVG + SMIL，视觉复杂 = Raster，两者之外放弃交互改用静态形式。

### SVG 层示例：可点击展开的图形装饰

当用户要求"点击展开"、"点击切换"等交互时，用 SVG + SMIL：

```html
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 580 200" style="width:100%;">
  <!-- 封面：点击后淡出 -->
  <rect x="0" y="0" width="580" height="200" fill="#e8784a">
    <animate attributeName="opacity"
             from="1" to="0"
             begin="click" dur="0.5s" fill="freeze"/>
  </rect>
  <text x="290" y="100" text-anchor="middle" fill="#fff"
        font-size="24" font-weight="bold">
    点击展开
    <animate attributeName="opacity"
             from="1" to="0"
             begin="click" dur="0.5s" fill="freeze"/>
  </text>

  <!-- 底层：点击后淡入 -->
  <rect x="0" y="0" width="580" height="200" fill="#2c3e50" opacity="0">
    <animate attributeName="opacity"
             from="0" to="1"
             begin="click" dur="0.5s" fill="freeze"/>
  </rect>
  <text x="290" y="100" text-anchor="middle" fill="#fff"
        font-size="18" opacity="0">
    这是隐藏内容！
    <animate attributeName="opacity"
             from="0" to="1"
             begin="click" dur="0.5s" fill="freeze"/>
  </text>
</svg>
```

**要点：**
- 所有元素**没有 `id="..."`**（微信过滤）
- `begin="click"` 是微信支持的 SMIL 事件
- `fill="freeze"` 让动画结束后保持最终状态（不回滚）
- 整个 svg 用 `style="width:100%;"` 自适应微信文章宽度

可以直接把这个 `<svg>` 塞进 `article.html` 字段，微信不会改动它。

### Raster 层的使用时机

当用户要求"炫酷 3D 翻转"、"CSS grid 仪表盘"、"渐变动画背景"等**绝对无法用 HTML 或 SVG 表达**的效果时：

1. **Stage 1 之前（当前）**：告诉用户"这种效果需要栅格化兜底，等 MBEditor 的 raster block 上线后可用。"或者先用 HTML2Canvas 在前端截图上传，作为静态图片插入。
2. **Stage 5 之后（可用后）**：用 MBDoc 的 `raster` block，传 `{"type":"raster","html":"...","css":"..."}`，后端会自动用 Playwright 渲染为 PNG。

### Publish Pipeline 陷阱速查

下面是 6 个已知陷阱的速查，详细排查指南和校准工具见 **[api-reference.md](api-reference.md) § 七**。

| # | 陷阱 | 症状 | 自动修复 |
|---|------|------|---------|
| 1 | `.reveal` / scroll-reveal | 内容隐形（`opacity:0`） | pipeline 改 `opacity=1`，strip transition |
| 2 | `position:absolute` | 装饰元素撑爆容器 | pipeline 转 `display:none` |
| 3 | `<a>` 外部链接 | 微信 strip 整个元素 | pipeline 转 `<section>`，URL 进"阅读原文" |
| 4 | grid/flex | — | ✅ v4.0 起完整支持，放心使用 |
| 5 | host-port shadowing | API 返回旧版本 | 排查 Windows 僵尸进程 |
| 6 | uvicorn 缓存旧字节码 | 改代码后 API 表现不变 | 重启容器 |

---

## 预览文章

告诉用户打开 Web 编辑器查看效果：
```
请打开 ${MBEDITOR_WEB_BASE:-http://localhost:7073}/editor/{article_id} 查看预览效果
```
