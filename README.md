# 灵鉴（LingJian）

面向「伪科学 / 风险内容」场景的识别与研判系统：后端串联 **OCR → BERT 多标签初判 → LLM 综合研判**，输出统一 JSON；配套 Vue 3 管理端、用户端与审核端。

## 仓库结构

| 目录 | 说明 |
| --- | --- |
| `backend/` | FastAPI 服务、数据库与任务队列、模型推理管线 |
| `fake-science-identify-all/` | **灵鉴门户（统一入口）**：角色导航，跳转至用户/管理/审核三端（开发默认 <http://127.0.0.1:3080>） |
| `fake-science-identify-user/` | 用户端（Vite + Vue 3 + Element Plus，默认 :3000） |
| `fake-science-identify-admin/` | 管理端（含 Excel 等能力，默认 :3001） |
| `fake-science-identify-audit/` | 审核端（默认 :3002） |
| `requirement.txt` | Python 依赖（推荐 Python **3.12**，见 `.python-version`） |
| `Bert/`、`models/` | BERT 检查点与本地 Qwen（如 `models/qwen/Qwen2.5-3B-Instruct`）等目录（按需放置） |

更完整的后端接口、环境变量、OCR/LLM 与 Windows 注意事项见 **[backend/README.md](backend/README.md)**。

## 环境要求

- **Python**：3.12（推荐）
- **Node.js**：用于门户与三个前端子项目（建议当前 LTS）
- **可选**：Redis（缓存；未启动时部分能力降级）、MySQL（生产数据库）、Elasticsearch（若启用搜索相关配置）

本地开发默认可使用 SQLite（见 `LINGJIAN_DATABASE_URL`，无需额外安装数据库即可启动后端）。

## 后端（FastAPI）

在**仓库根目录**安装依赖并启动（请将路径换成你的本机仓库路径）：

```powershell
cd D:\LingJian
py -3.12 -m pip install -r requirement.txt
py -3.12 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

- 接口文档：<http://127.0.0.1:8000/docs>
- 健康检查：`GET /health`

若仅需文本分析、不跑图文与 OCR，可按根目录 `requirement.txt` 内注释说明，自行注释掉 Paddle 相关依赖行后再安装。

## 前端（Vue 3 + Vite）

### 一键开发（推荐）

在仓库根执行 `scripts\start-dev.bat` 或：

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-dev.ps1
```

会依次启动：后端、**门户 :3080**、用户端 :3000、管理端 :3001、审核端 :3002。浏览器请打开 **<http://127.0.0.1:3080>** 作为大系统主页，从门户进入各子系统。

门户跳转地址由 `fake-science-identify-all/.env.development` 中的 `VITE_*_APP_ORIGIN` 配置（生产部署请改为实际域名）。

### 单独启动某一端

各子项目独立安装与启动（端口以各包内 `vite.config` 为准）：

```powershell
cd D:\LingJian\fake-science-identify-all
npm install
npm run dev
# 门户默认 http://127.0.0.1:3080

cd D:\LingJian\fake-science-identify-user
npm install
npm run dev
```

对 `fake-science-identify-admin`、`fake-science-identify-audit` 同理。

生产构建：`npm run build`，产物在各自 `dist/`。

## 相关文档

- [backend/README.md](backend/README.md) — 分析流水线、主要 API、`LINGJIAN_*` 环境变量、冒烟脚本与依赖版本说明
