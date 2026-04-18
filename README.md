<div align="center">

# MBEditor

### 让 Agent 直接写出、排版并投递微信公众号文章

**不是只会生成文案，而是把公众号内容生产流程真正跑通。**

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-One%20Command-2496ED.svg)](docker-compose.yml)
[![Agent](https://img.shields.io/badge/Agent-Claude%20%7C%20Codex%20%7C%20OpenClaw-8B5CF6.svg)](skill/mbeditor.skill.md)
[![Version](https://img.shields.io/badge/Version-v3.0-E8553A.svg)](https://github.com/AAAAAnson/mbeditor/releases)

</div>

---

> MBEditor 不是“给 AI 加个写稿按钮”的编辑器。  
> 它是一套面向 Agent 工作流设计的微信公众号内容生产系统。

![MBEditor 编辑器界面](docs/screenshots/editor-v3.png)

## 先用一句话理解它

如果你希望 Agent 不只是帮你写一段文案，而是继续完成排版、处理图片、预览效果、投递微信草稿箱，那么 MBEditor 就是这层基础设施。

## MBEditor 是什么

MBEditor 是一个面向微信公众号内容生产的编辑与发布系统。

它最核心的差异，不是单纯支持富文本编辑，也不是只会生成文案，而是把公众号内容生产流程拆成了一套 **可以被 Agent 直接调用的能力层**。

这意味着 Claude Code、Codex、OpenClaw 这类 Agent 不只是“帮你写一篇文章”，而是可以继续往下完成：

- 创建文章
- 写入正文
- 选择或调整排版
- 上传图片
- 处理微信兼容样式
- 预览最终效果
- 投递到微信公众号草稿箱

如果你想做的是 **Agent 驱动的公众号工作流**，而不是一个更花哨的手工编辑器，MBEditor 才真正有价值。

## 它解决的不是“写作”，而是整条生产链路

大多数公众号编辑工具主要服务人工操作。
大多数 AI 写作工具主要停留在生成文案。

但真实的问题其实在中间断掉了：

- Agent 很难稳定操作复杂网页 UI
- 生成内容之后，排版、图片、样式兼容、发布仍然是断开的
- 很多“AI 公众号工具”只能给你一段文字，不能给你最终成品

MBEditor 解决的是这条链路的可执行性：

| 环节 | 普通方案常见问题 | MBEditor 的做法 |
|------|------------------|----------------|
| 写作 | 只产出正文，缺少后续动作 | 文章创建与内容写入 API 化 |
| 排版 | AI 生成内容难以稳定落版 | 支持 HTML / Markdown / 可视化编辑 |
| 图片 | 上传与引用流程断裂 | 图片接口独立可调用 |
| 发布 | 最后一步仍需人工进入后台 | 支持投递到微信草稿箱 |
| Agent 接入 | 大量依赖点击 UI | 提供 REST API + Skill |

一句话说，MBEditor 不是只解决“写”，而是要让 Agent **真的把一篇公众号文章做完**。

## 为什么 MBEditor 值得关注

### 1. Agent First
MBEditor 从设计上就不是“人点一下，AI 帮一点”。
它的核心能力是可调用、可编排、可嵌入流程的，这才是 Agent 时代真正有价值的方向。

### 2. 不是半成品能力
很多工具只能解决其中一段，比如只会写文案、只会做 Markdown、只会提供一个编辑器。
MBEditor 的方向是把写作、排版、预览、发布串起来，减少链路断点。

### 3. 同时保留人工可控性
它不是纯自动化黑箱。
你既可以让 Agent 全自动执行，也可以自己进入编辑器手工微调，最后再投递。

## 核心能力

- **Agent 可调用**：适配 Claude Code、Codex、OpenClaw 等 Agent 工作流
- **完整 REST API**：文章、图片、发布、配置都有明确接口
- **多种编辑模式**：HTML、Markdown、可视化编辑并存
- **适配微信生态**：处理样式兼容、图片上传、草稿投递
- **高自由度排版**：支持直接控制 HTML / CSS / JS
- **可接入自动化系统**：适合进入脚本、定时任务、CI 或内部内容流程

## 适合谁

MBEditor 更适合这些场景：

### 内容团队
需要批量、标准化地产出公众号内容，希望把选题到草稿的流程做成半自动或全自动。

### 开发者 / AI 工具构建者
希望把公众号内容生产接入 Agent 或内容系统，而不是停留在“生成一段文案”。

### 对排版成品要求高的人
不仅要能写，还要能做出真正能发的公众号排版，而不是普通文本输出。

### 需要可控流程的人
希望既能自动执行，也能在最后人工检查、修稿、微调。

如果你只是偶尔手工写一篇文章，对 API、Agent 和自动化没有需求，那 MBEditor 的优势不会完全体现出来。

## 三个典型使用场景

### 场景 1：技术公众号
你给 Agent 一个主题，比如 Docker、RAG、AI Coding、产品复盘，它自动完成：

- 起标题
- 写正文
- 套用技术风格排版
- 插入封面或配图
- 投递到微信草稿箱

适合个人开发者、技术团队、独立创作者。

### 场景 2：品牌内容批量生产
团队每周要产出多篇内容，希望先用统一模板生成初稿，再由运营二次修改后发出。

适合有固定栏目、固定节奏、固定视觉规范的内容团队。

### 场景 3：内容工作流接入自动化系统
把 MBEditor 接入内部系统，让选题库、素材库、Agent、排版引擎、发布流程串起来，而不是每一步都手工切换工具。

适合希望把内容生产系统化的团队，而不是只追求单次提效。

## 你实际会怎么用它

你可以直接对 Agent 下这样的命令：

```bash
claude "写一篇关于 Docker 入门的公众号文章，面向新手，风格清晰克制，做好排版，并投递到微信草稿箱"
```

MBEditor 负责底层能力，Agent 负责把这些能力串成流程。

最终拿到的不是一段“待处理文本”，而是一篇更接近可直接发送的公众号成品。

## 快速开始

### 1. 部署 MBEditor

```bash
git clone https://github.com/AAAAAnson/mbeditor.git
cd mbeditor
docker compose up -d
```

启动完成后：

- 编辑器界面: `http://localhost:7073`
- API 接口: `http://localhost:7072/api/v1`

更新版本：

```bash
git pull
docker compose up --build -d
```

> 文章和图片默认保存在 `data/` 目录，更新不会直接清空内容。

### 2. 安装 Agent Skill

MBEditor 提供了 `skill/mbeditor.skill.md`，可以直接接入 Agent。

#### Claude Code

项目内直接使用：

```bash
cd mbeditor
claude "帮我写一篇公众号文章，排版清晰，并投递到草稿箱"
```

全局安装：

```bash
# macOS / Linux
mkdir -p ~/.claude/skills
cp skill/mbeditor.skill.md ~/.claude/skills/mbeditor.skill.md

# Windows
mkdir %USERPROFILE%\.claude\skills
copy skill\mbeditor.skill.md %USERPROFILE%\.claude\skills\mbeditor.skill.md
```

#### Codex

```bash
# macOS / Linux
mkdir -p ~/.codex/agents
cp skill/mbeditor.skill.md ~/.codex/agents/mbeditor.skill.md

# 使用
codex "调用 MBEditor 写一篇公众号文章，并完成排版"
```

#### OpenClaw

```bash
openclaw skill add ./skill/mbeditor.skill.md
openclaw "写一篇公众号文章，主题是 Docker 入门，并完成排版和草稿投递"
```

### 3. 配置微信公众号（可选）

如果要直接投递到微信草稿箱，需要配置公众号 AppID 和 AppSecret：

```bash
curl -X PUT http://localhost:7072/api/v1/config \
  -H "Content-Type: application/json" \
  -d '{"appid":"你的appid","appsecret":"你的appsecret"}'
```

## Agent Demo

下面是一个最小可执行流程。
这部分不是概念展示，而是 MBEditor 真正有价值的地方：它让 Agent 能稳定调用公众号生产链路里的关键动作。

```bash
# 1. 创建文章
curl -X POST http://localhost:7072/api/v1/articles \
  -H "Content-Type: application/json" \
  -d '{"title":"AI 写作指南","mode":"html"}'

# 2. 写入内容
curl -X PUT http://localhost:7072/api/v1/articles/{id} \
  -d '{"html":"<h1>AI 写作指南</h1><p>正文...</p>","css":"h1{color:#333}"}'

# 3. 上传图片
curl -X POST http://localhost:7072/api/v1/images/upload \
  -F "file=@cover.png"

# 4. 投递草稿
curl -X POST http://localhost:7072/api/v1/publish/draft \
  -d '{"article_id":"你的文章ID"}'
```

这意味着 MBEditor 可以被接进：

- Agent 自动写作流程
- 定时内容生产任务
- 内部运营工具链
- CI / 自动化发布系统

## 编辑与排版能力

![预览模式](docs/screenshots/preview-v3.png)

如果你只想生成文字，很多工具都能做。
但如果你想要的是“可发布成品”，编辑与排版层就是不能省的部分。

### 编辑模式

- **HTML 模式**：适合设计师、开发者、Agent，精细控制版式
- **Markdown 模式**：适合快速写作和结构化内容
- **可视化编辑**：适合人工微调和最终检查

### 可做出的版式类型

MBEditor 支持高自由度的 HTML 版式表达，适合公众号常见样式，例如：

- 标签块
- 强调卡片
- 数据展示模块
- 时间线
- 分栏内容
- 对比区块

这点很关键，因为很多“AI 写文章”工具最后只能给出一坨文字，真正能发出去的成品还得重新做。

## 排版示例

MBEditor + AI 可以直接产出不同风格的公众号版式。

<table>
<tr>
<td align="center" width="33%"><strong>明亮清新</strong></td>
<td align="center" width="33%"><strong>暗黑终端</strong></td>
<td align="center" width="34%"><strong>报纸编辑部</strong></td>
</tr>
<tr>
<td><img src="docs/screenshots/preview.png" alt="明亮清新" /></td>
<td><img src="docs/screenshots/design-v1-terminal.png" alt="暗黑终端" /></td>
<td><img src="docs/screenshots/design-v2-newspaper.png" alt="报纸编辑部" /></td>
</tr>
<tr>
<td align="center" width="33%"><strong>霓虹赛博</strong></td>
<td align="center" width="33%"><strong>大地暖色</strong></td>
<td align="center" width="34%"><strong>瑞士极简</strong></td>
</tr>
<tr>
<td><img src="docs/screenshots/design-v3-neon.png" alt="霓虹赛博" /></td>
<td><img src="docs/screenshots/design-v4-earth.png" alt="大地暖色" /></td>
<td><img src="docs/screenshots/design-v5-swiss.png" alt="瑞士极简" /></td>
</tr>
</table>

## API 概览

### 文章
- `POST /api/v1/articles` 创建文章
- `GET /api/v1/articles` 获取文章列表
- `GET /api/v1/articles/{id}` 获取文章详情
- `PUT /api/v1/articles/{id}` 更新文章
- `DELETE /api/v1/articles/{id}` 删除文章

### 图片
- `POST /api/v1/images/upload` 上传图片
- `GET /api/v1/images` 获取图片列表
- `DELETE /api/v1/images/{id}` 删除图片

### 发布
- `POST /api/v1/publish/draft` 投递到微信草稿箱
- `POST /api/v1/publish/preview` 预览处理结果
- `POST /api/v1/publish/process` 处理图片与微信兼容内容
- `GET /api/v1/publish/html/{id}` 获取处理后的 HTML

### 配置
- `GET /api/v1/config` 查看配置状态
- `PUT /api/v1/config` 配置微信公众号 AppID / AppSecret

## 技术栈

- Frontend: React 19 + TypeScript + Tailwind CSS 4
- Backend: FastAPI + Python
- Infra: Docker Compose + Nginx
- Editor: Monaco Editor
- Media: Pillow
- Publish: 微信公众号 API

## 项目结构

```text
mbeditor/
├─ frontend/
├─ backend/
├─ skill/
├─ docs/
├─ data/
├─ docker-compose.yml
└─ LICENSE
```

## 接下来建议你先看什么

如果你是第一次打开这个项目，建议按这个顺序看：

1. 先看“它解决的不是写作，而是整条生产链路”
2. 再看“你实际会怎么用它”
3. 再看 Agent Demo 和排版示例
4. 最后再决定是否接入你的工作流

## 贡献

欢迎提交 Issue 和 Pull Request：

- Issues: <https://github.com/AAAAAnson/mbeditor/issues>
- Pull Requests: <https://github.com/AAAAAnson/mbeditor/pulls>

项目地址：<https://github.com/AAAAAnson/mbeditor>

## License

MIT © Anson
