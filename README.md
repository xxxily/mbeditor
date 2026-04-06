# MBEditor

微信公众号文章编辑器 — 所见即所得编辑、实时预览、一键推送草稿箱。

## 功能

- **HTML 可视化编辑** — 基于 contentEditable iframe，所见即所得
- **Monaco 代码编辑器** — 直接编辑 HTML/CSS 源码
- **Markdown 模式** — 支持 Markdown 编写，主题化渲染
- **实时预览** — 模拟微信公众号排版效果
- **图床管理** — 上传图片自动获取微信永久素材链接
- **一键推送** — 直接发布到微信公众号草稿箱
- **CSS Inline 化** — 自动将样式内联，确保微信兼容性

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | React 19 + TypeScript + Tailwind CSS 4 + Vite 6 |
| 后端 | FastAPI + Python |
| 部署 | Docker Compose |

## 快速开始

### 前置要求

- Docker & Docker Compose
- 微信公众号 AppID 和 AppSecret（[申请指南](https://mp.weixin.qq.com/)）

### 部署

```bash
# 1. 克隆仓库
git clone https://github.com/anson-momo/mbeditor.git
cd mbeditor

# 2. 配置微信凭据
cp data/config.json.example data/config.json
# 编辑 data/config.json，填入你的 appid 和 appsecret

# 3. 启动服务
docker compose up -d
```

访问 `http://localhost:7070` 开始使用。

### 本地开发

```bash
# 前端
cd frontend
npm install
npm run dev

# 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 7071
```

## 项目结构

```
mbeditor/
├── frontend/          # React 前端
│   └── src/
│       ├── pages/     # 编辑器、文章列表、设置
│       └── components/# UI 组件
├── backend/           # FastAPI 后端
│   └── app/
│       ├── api/v1/    # REST API (文章/图片/发布/微信)
│       └── services/  # 微信 API 服务
├── data/              # 运行时数据 (gitignored)
└── docker-compose.yml
```

## API

| 端点 | 说明 |
|------|------|
| `GET/POST /api/v1/articles` | 文章 CRUD |
| `POST /api/v1/images/upload` | 上传图片到微信素材库 |
| `POST /api/v1/publish/draft` | 推送到草稿箱 |
| `GET /api/v1/wechat/config` | 微信配置管理 |

## 许可证

[MIT](LICENSE)
