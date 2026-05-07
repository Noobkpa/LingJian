# 灵鉴后端 · 前端对接说明

本文描述 HTTP API 的基址、鉴权方式与各接口要点，便于 Web / 移动端联调。服务端框架为 **FastAPI**，默认会在根路径提供交互式文档：**`GET /docs`**（Swagger UI）、**`GET /redoc`**。

---

## 1. 基础约定

| 项 | 说明 |
|----|------|
| **API 根前缀** | 默认 **`/api/v1`**。部署方可通过环境变量 `LINGJIAN_API_PREFIX` 修改，联调前请与后端确认实际前缀。 |
| **Base URL 示例** | `http://127.0.0.1:8000`（开发） |
| **完整路径示例** | `{BASE}{前缀}/auth/login` → `http://127.0.0.1:8000/api/v1/auth/login` |
| **字符编码** | UTF-8；JSON 请求使用 `Content-Type: application/json` |
| **跨域** | 当前后端对浏览器侧配置了宽松 CORS（`allow_origins=["*"]`），生产环境应由网关收敛 |

下文路径均省略 `{BASE}`，写作 **`/api/v1/...`**（若前缀被改过，请替换为你的前缀）。

---

## 2. 鉴权（JWT）

### 2.1 请求头

除公开接口（注册、登录、健康检查）外，受保护接口需在 Header 中携带访问令牌：

```http
Authorization: Bearer <access_token>
```

`access_token` 来自登录或注册接口响应；过期后使用 **`refresh_token`** 调用刷新接口换取新的令牌对。

### 2.2 令牌响应结构（注册 / 登录 / 刷新）

```json
{
  "access_token": "<JWT>",
  "refresh_token": "<JWT>",
  "token_type": "bearer"
}
```

### 2.3 默认 RBAC 角色与权限（种子数据）

后端首次初始化数据库时会写入角色与权限。**普通注册用户**默认绑定 **`user`** 角色，具备：

- `analyze:run` — 调用同步分析接口  
- `content:upload` — 文本/图片/混合入库并异步分析  

其他权限示例：

| 权限标识 | 含义 |
|----------|------|
| `content:batch` | ZIP 批量入库 |
| `review:read` | 查看审核队列 |
| `review:write` | 审核通过/驳回 |
| `admin:stats` | 管理端统计、角色列表 |
| `admin:export` | 发起异步导出 |

缺少权限时接口返回 **403**，详见下文错误说明。

---

## 3. 通用响应与错误

### 3.1 业务异常（`AppException`）

响应体符合统一结构（便于前端展示与国际化键）：

```json
{
  "code": "DUPLICATE",
  "message": "用户名已存在",
  "detail": null,
  "request_id": "<可选，请求追踪 ID>"
}
```

响应头中可能包含 **`X-Request-ID`**，可与后端日志对齐排障。

### 3.2 参数校验失败（422）

```json
{
  "code": "VALIDATION_ERROR",
  "message": "请求参数无效",
  "detail": [ ... ],
  "request_id": "..."
}
```

### 3.3 FastAPI / Starlette 默认错误（401 等）

部分路由仍使用框架自带的 **`{"detail": "..."}`** 形式（例如登录失败）。前端应对 **`detail`** 与上面的 **`message`** 两种字段都做兼容展示。

### 3.4 限流

全局限流默认约为 **每 key 每秒请求次数上限**（环境变量 `LINGJIAN_RATE_LIMIT_PER_SECOND`，默认 10）。限流 key 与 **客户端 IP** 及 **`Authorization`** 内容相关；触发时返回 **429**（由 slowapi 处理）。

---

## 4. 接口一览

以下表格中「权限」列为所需权限码；**登录即可**表示仅需有效 `Bearer` token，无额外 RBAC 码（但默认用户仍须先注册/登录）。

### 4.1 健康检查（无前缀）

| 方法 | 路径 | 鉴权 |
|------|------|------|
| GET | `/health` | 无 |

响应示例：`{"status":"ok","app":"Lingjian Backend"}`

---

### 4.2 认证 ` /api/v1/auth`

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| POST | `/api/v1/auth/register` | 无 | 注册；成功后直接返回一对 JWT |
| POST | `/api/v1/auth/login` | 无 | 登录 |
| POST | `/api/v1/auth/refresh` | 无 |  body：`{"refresh_token":"..."}` |

**注册 / 登录请求体**

```json
// register
{ "username": "string", "password": "string", "email": "string | null" }

// login
{ "username": "string", "password": "string" }
```

---

### 4.3 当前用户 ` /api/v1/users`

| 方法 | 路径 | 鉴权 |
|------|------|------|
| GET | `/api/v1/users/me` | Bearer |

响应（`UserPublic`）：`id`, `username`, `email`。

---

### 4.4 角色（管理）` /api/v1/roles`

| 方法 | 路径 | 权限 |
|------|------|------|
| GET | `/api/v1/roles` | `admin:stats` |

响应为角色数组：`id`, `name`, `description`。

---

### 4.5 同步分析 ` /api/v1/analyze`

在同一请求内完成 OCR → BERT → LLM（耗时可能较长）。均需 **`analyze:run`**。

| 方法 | 路径 | Content-Type | 说明 |
|------|------|----------------|------|
| POST | `/api/v1/analyze/text` | `application/json` | body 见下 |
| POST | `/api/v1/analyze/image` | `multipart/form-data` | 字段 `file`（图片）；可选表单字段 `content_id` |
| POST | `/api/v1/analyze/mixed` | `multipart/form-data` | 字段 `text`（可选）、`file`（图片）；可选 `content_id` |

**文本分析 JSON**

```json
{
  "text": "待检测文本",
  "content_id": "可选，不传则由服务端生成"
}
```

**成功响应**为 `AnalyzeResponse`（字段较多），核心字段包括：

- `content_id`, `modality`（`text` | `image` | `mixed`）
- `input_text`（合并后的用于判定文本）
- `ocr`, `bert`, `llm`（各模块明细）
- `final`：`risk_level`, `score`, `basis`, `features`
- **`standard_judgment`**：面向产品/大屏的**固定结构研判 JSON**（见下一小节）
- `meta`：附加信息（如编排追踪）

#### `standard_judgment`（固定结构，推荐前端主展示）

与系统设计文档对齐；**`infer_time` 由服务端在流水线结束时写入**（时区默认 `Asia/Shanghai`，可用环境变量 `LINGJIAN_INFER_TZ` 覆盖）。`risk_level` 仅为 **`高` | `中` | `低`**（与内部 `final.risk_level` 使用的「高风险」等文案区分）。

```json
{
  "content_id": "同 AnalyzeResponse.content_id",
  "risk_level": "高",
  "comprehensive_score": 95,
  "logical_fallacy": "因果谬误……",
  "scientific_error": "……正确方向说明",
  "core_features": ["绝对化用语", "科学事实错误"],
  "judgment_basis": "……综合判定依据",
  "infer_time": "2026-03-01 10:00:08"
}
```

LLM 启用时，`logical_fallacy`、`scientific_error`、`core_features`、`judgment_basis` 尽量来自模型 JSON；若启发式/兜底路径字段为空，服务端会用基于 BERT 命中标签等的**保守占位文案**补齐，避免前端拿到空串。

单图上传有大小与格式限制（默认最大约 **20MB**，扩展名 png/jpg/jpeg/bmp/webp，且会做魔数校验）。

---

### 4.6 异步入库与分析 ` /api/v1/contents`

先写入 **`contents`** 表并入 **Celery** 队列，适合批量或后台处理。返回 **`task_id`**（Celery 任务 ID）用于轮询。

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| POST | `/api/v1/contents/text` | `content:upload` | JSON：`{"text":"..."}` |
| POST | `/api/v1/contents/image` | `content:upload` | `multipart`：`file` |
| POST | `/api/v1/contents/mixed` | `content:upload` | `multipart`：`text` + `file` |
| POST | `/api/v1/contents/batch_zip` | `content:batch` | `multipart`：单个 `.zip`，解压后为多张图片 |

**异步接口典型响应**

```json
{
  "content_id": "<公开 ID>",
  "job_id": 1,
  "task_id": "<Celery id>"
}
```

ZIP 接口返回 `count` 与 `items` 数组（每项同上）。

---

### 4.7 任务查询 ` /api/v1/tasks`

| 方法 | 路径 | 鉴权 |
|------|------|------|
| GET | `/api/v1/tasks/{task_id}` | Bearer |

`task_id` 为 Celery 返回的 ID。响应包含 `state`（如 PENDING/SUCCESS/FAILURE）、成功时的 `result`，若任务与当前用户的数据关联，还会附带 `content_id`、`job_status` 或导出相关信息。

---

### 4.8 管理统计 ` /api/v1/admin/stats`

均需 **`admin:stats`**。

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/admin/stats/overview` | 用户数、内容数、结果条数等汇总 |
| GET | `/api/v1/admin/stats/risk_buckets` | 按最终风险标签聚合桶 |
| GET | `/api/v1/admin/stats/daily` | 查询参数 `days`（默认 7），按日粗略计数 |

---

### 4.9 审核 ` /api/v1/review`

| 方法 | 路径 | 权限 |
|------|------|------|
| GET | `/api/v1/review/queue` | `review:read` |
| POST | `/api/v1/review/action` | `review:write` |

**队列查询参数**：`page`, `page_size`。

**审核动作 body**

```json
{
  "public_id": "<内容的 content_id / public_id>",
  "action": "approve"
}
```

`action` 取值：`approve` | `reject`。

---

### 4.10 搜索（Elasticsearch）` /api/v1/search`

| 方法 | 路径 | 鉴权 |
|------|------|------|
| GET | `/api/v1/search` | Bearer |

**查询参数**：`q`（必填）、`page`、`page_size`。  
仅检索**当前登录用户**名下数据；若后端未配置 ES，返回 **503**。

---

### 4.11 异步导出 ` /api/v1/exports`

| 方法 | 路径 | 权限 |
|------|------|------|
| POST | `/api/v1/exports` | `admin:export` |

响应包含 `export_id` 与 Celery `task_id`，再通过 **`GET /api/v1/tasks/{task_id}`** 轮询；完成后 `file_path` 等字段可在任务查询结果中出现（具体以后端实现为准）。

---

## 5. 前端实现建议

1. **集中封装 HTTP 客户端**：Base URL、超时、`Authorization` 注入、`401` 时跳转登录或尝试 `refresh`（需自行设计刷新队列，避免并发重复刷新）。  
2. **保存双令牌**：`access_token` 用于常规请求；`refresh_token` 仅存安全存储（httpOnly Cookie 由后端配合时更佳）。  
3. **长耗时接口**：同步分析可能数十秒～数分钟，请使用足够长的 **timeout**，并考虑 Loading / 取消策略；异步场景优先走 **`/contents/*` + `/tasks/{id}`**。  
4. **错误展示**：同时兼容 **`code` + `message`** 与 **`detail`** 字符串 / 数组。  
5. **联调清单**：与后端确认 **`LINGJIAN_API_PREFIX`**、是否启用 HTTPS、以及生产环境的 **CORS** 白名单。

---

## 6. 变更记录

- 文档与后端仓库中的路由代码同步维护；若接口有变更，请以 **`/docs` OpenAPI** 为准或要求后端更新本文。
