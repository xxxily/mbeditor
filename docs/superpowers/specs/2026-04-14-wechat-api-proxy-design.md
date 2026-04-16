# 微信 API 代理配置设计文档

**日期**: 2026-04-14
**状态**: Draft
**作者**: Sisyphus

---

## 背景

公众号微信 API（`api.weixin.qq.com`）调用需要 IP 白名单。开发者本地开发时出口 IP 不固定，无法配置白名单。已有线上服务器可提供 HTTP/HTTPS 代理服务，通过代理转发微信 API 请求，使出口 IP 固定为服务器 IP。

## 目标

- 让所有微信 API 调用通过可配置的 HTTP/HTTPS 代理发出
- 代理地址通过前端设置页面配置，存储在 config.json 中
- 代理配置为空时保持现有直连行为（向后完全兼容）
- 最小代码改动，不影响现有功能

## 非目标

- 不实现代理健康检查/自动故障转移
- 不实现 Nginx 反向代理层（属于部署侧）
- 不代理非微信 API 的外部请求（如外部图片下载保持直连）

---

## 架构设计

### 1. HTTP 客户端工厂

在 `wechat_service.py` 中新增 `get_http_client()` 函数，根据配置返回带代理或不带代理的 httpx 客户端。

```python
# wechat_service.py

_proxy_client_cache: dict = {}  # proxy_url -> httpx.Client

def get_http_client() -> httpx.Client:
    """获取 httpx 客户端，根据配置决定是否使用代理。"""
    config = load_config()
    proxy = config.get("proxy_url") or None
    cache_key = proxy or "__no_proxy__"
    
    if cache_key not in _proxy_client_cache:
        _proxy_client_cache[cache_key] = httpx.Client(
            proxy=proxy, 
            timeout=30
        )
    return _proxy_client_cache[cache_key]
```

**设计决策：同步客户端**

当前 `wechat_service.py` 中直接使用 `httpx.post()`（同步模式），因此工厂函数返回同步 `httpx.Client`，保持现有调用模式不变。

### 2. 配置扩展

`config.json` 结构扩展：

```json
{
  "appid": "wx1234567890",
  "appsecret": "...",
  "proxy_url": "https://your-proxy-server:port"
}
```

- `proxy_url` 为空字符串或不存在时：直连（向后兼容）
- `proxy_url` 为 `http://...` 或 `https://...`：通过代理

### 3. 数据流

```
前端设置页 (Settings.tsx)
  → PUT /api/v1/config { appid, appsecret, proxy_url }
    → wechat.py: update_config
      → wechat_service.save_config(appid, appsecret, proxy_url)
        → 写入 config.json
        → 清除 token 缓存（触发重新获取）

所有微信 API 调用
  → get_http_client()
    → 读取 config.json 获取 proxy_url
    → 创建/复用 httpx.Client(proxy=proxy_url)
    → 通过 client.post() / client.get() 发出请求
```

---

## 组件设计

### 后端改动

#### `wechat_service.py`

| 改动 | 描述 |
|------|------|
| `save_config(appid, appsecret, proxy_url)` | 增加 `proxy_url` 参数，写入 config.json |
| `get_http_client()` | 新增：根据 config 创建/复用 httpx.Client |
| `get_access_token()` | 修改：使用 `get_http_client().post()` 替代 `httpx.post()` |
| `_post_with_token_retry()` | 修改：使用 `get_http_client()` 替代裸 `httpx.post()` |
| `process_html_images()` 中的 `httpx.get()` | 修改：使用 `get_http_client()` |

#### `wechat.py` (API 路由)

| 改动 | 描述 |
|------|------|
| `ConfigReq` 模型 | 增加 `proxy_url: str = ""` 字段（可选） |
| `get_config()` | 返回值增加 `proxy_url` 字段（不脱敏，因为代理地址非敏感） |
| `update_config()` | 接收并传递 `proxy_url` 给 `save_config()` |

### 前端改动

#### `Settings.tsx`

| 改动 | 描述 |
|------|------|
| 新增 `proxyUrl` 状态 | `useState("")`，初始值从 `/config` 接口获取 |
| `save()` 函数 | 请求体增加 `proxy_url` 字段 |
| `useEffect` | 从接口响应中读取并设置 `proxyUrl` |

#### `WechatConfigSection.tsx`

| 改动 | 描述 |
|------|------|
| Props 增加 `proxyUrl`、`onProxyUrlChange` | 传递代理地址状态 |
| 新增代理地址输入框 | 在 AppSecret 输入框下方，占位符提示为可选 |

---

## 错误处理

| 场景 | 行为 |
|------|------|
| 代理地址为空 | 保持直连，与当前行为完全一致 |
| 代理地址格式无效 | httpx 抛出连接异常，被现有 `AppError` 捕获 |
| 代理服务器不可达 | 请求超时，抛出 `AppError(code=500, message="...")` |
| HTTPS 代理证书问题 | httpx 默认验证 SSL，用户需自行保证代理证书有效 |
| 代理认证（用户名密码） | 支持 `http://user:pass@host:port` 格式 |

---

## 安全性考虑

1. **代理 URL 不脱敏**：代理地址不是敏感凭据，API 响应中返回完整值，前端可直接回显
2. **appid/appsecret 保持脱敏**：GET `/config` 返回的 appsecret 仍 masked（`****1234`）
3. **本地存储**：config.json 仍只存储在服务器本地 filesystem，不通过网络传输
4. **代理信任**：用户可以控制使用哪个代理服务器，建议仅在可信环境中配置

---

## 测试策略

### 后端单元测试

1. `get_http_client()` 无代理时创建不带 proxy 的 client
2. `get_http_client()` 有代理时创建带 proxy 的 client
3. `get_http_client()` 相同代理返回缓存实例
4. `get_http_client()` 不同代理创建新实例
5. `save_config()` 写入 proxy_url 到 config.json
6. 代理不可达时，现有错误处理链路正常工作

### 前端测试

1. 渲染时 proxyUrl 从接口正确加载
2. 输入代理地址后正确传递给 onChange
3. 保存时请求体包含 proxy_url 字段
4. 清空代理地址后保存，proxy_url 为空字符串

---

## 文件改动清单

| 文件 | 类型 | 估计行数变化 |
|------|------|-------------|
| `backend/app/services/wechat_service.py` | 修改 | +25, ~5 改 |
| `backend/app/api/v1/wechat.py` | 修改 | +3 |
| `backend/tests/test_wechat_config.py` | 新增 | +50 |
| `frontend/src/pages/Settings.tsx` | 修改 | +10 |
| `frontend/src/components/settings/WechatConfigSection.tsx` | 修改 | +20 |

---

## 向后兼容性

- **config.json 向后兼容**：旧 config 无 `proxy_url` 字段，`config.get("proxy_url")` 返回 None，等效于无代理
- **API 向后兼容**：`ConfigReq` 的 `proxy_url` 字段可选（默认 `""`），不传则不修改代理配置
- **调用链不变**：外部调用者（Agent、CLI）不受影响，仅内部实现改动
