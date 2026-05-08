from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]

# 仓库内可选放置通义千问 3B（Qwen2.5-3B-Instruct）；存在则默认走真实 LLM，也可用 LINGJIAN_LLM_MODEL 覆盖。
LOCAL_QWEN_WEIGHTS_DIR = PROJECT_ROOT / "models" / "qwen" / "Qwen2.5-3B-Instruct"


def _local_qwen_available() -> bool:
    return LOCAL_QWEN_WEIGHTS_DIR.is_dir() and (LOCAL_QWEN_WEIGHTS_DIR / "config.json").is_file()


def _default_llm_model() -> str:
    if _local_qwen_available():
        return str(LOCAL_QWEN_WEIGHTS_DIR.resolve())
    return "qwen/Qwen2.5-3B-Instruct"


def _default_enable_llm_flag() -> str:
    return "1" if _local_qwen_available() else "0"


class Settings:
    app_name: str = "Lingjian Backend"
    # 对外 API 前缀（计划：`/api/v1`）；可通过环境变量覆盖以保持兼容。
    api_prefix: str = os.getenv("LINGJIAN_API_PREFIX", "/api/v1")
    upload_dir: Path = PROJECT_ROOT / "backend" / "uploads"
    bert_checkpoint: Path = Path(
        os.getenv(
            "LINGJIAN_BERT_CHECKPOINT",
            str(PROJECT_ROOT / "Bert" / "bert_chinese_multilabel_out" / "best"),
        )
    )
    bert_max_length: int = int(os.getenv("LINGJIAN_BERT_MAX_LENGTH", "512"))
    bert_chunk_chars: int = int(os.getenv("LINGJIAN_BERT_CHUNK_CHARS", "512"))
    bert_chunk_overlap: int = int(os.getenv("LINGJIAN_BERT_CHUNK_OVERLAP", "0"))
    ocr_device: str = os.getenv("LINGJIAN_OCR_DEVICE", "gpu")
    ocr_score_threshold: float = float(os.getenv("LINGJIAN_OCR_SCORE_THRESHOLD", "0.6"))
    enable_llm: bool = os.getenv(
        "LINGJIAN_ENABLE_LLM",
        _default_enable_llm_flag(),
    ).lower() in {"1", "true", "yes", "on"}
    # local：加载仓库内/本机 Qwen 权重；external：调用 OpenAI-compatible Chat Completions API。
    llm_provider: str = os.getenv("LINGJIAN_LLM_PROVIDER", "local").strip().lower()
    llm_model: str = os.getenv("LINGJIAN_LLM_MODEL", _default_llm_model())
    # 结构化研判 JSON（含多段中文说明）；默认 384 兼顾完整性与耗时；可用 LINGJIAN_LLM_MAX_NEW_TOKENS 覆盖
    llm_max_new_tokens: int = int(os.getenv("LINGJIAN_LLM_MAX_NEW_TOKENS", "384"))
    _adapter_raw = os.getenv("LINGJIAN_LLM_ADAPTER", "").strip()
    llm_adapter_dir: Path | None = (
        Path(_adapter_raw).resolve() if _adapter_raw else None
    )
    external_llm_base_url: str = os.getenv(
        "LINGJIAN_EXTERNAL_LLM_BASE_URL",
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
    ).strip()
    external_llm_api_key: str = os.getenv("LINGJIAN_EXTERNAL_LLM_API_KEY", "").strip()
    external_llm_model: str = os.getenv("LINGJIAN_EXTERNAL_LLM_MODEL", "qwen-plus").strip()
    external_llm_timeout_sec: float = float(os.getenv("LINGJIAN_EXTERNAL_LLM_TIMEOUT", "120"))
    external_llm_max_tokens: int = int(os.getenv("LINGJIAN_EXTERNAL_LLM_MAX_TOKENS", "1024"))
    external_llm_json_mode: bool = os.getenv(
        "LINGJIAN_EXTERNAL_LLM_JSON_MODE", "0"
    ).lower() in {"1", "true", "yes", "on"}

    # --- 企业级：数据库 / 缓存 / 消息队列 / 搜索 ---
    # 默认 SQLite 便于本地开发；生产请使用 MySQL，例如
    # mysql+pymysql://user:pass@host:3306/lingjian?charset=utf8mb4
    database_url: str = os.getenv(
        "LINGJIAN_DATABASE_URL",
        f"sqlite:///{(PROJECT_ROOT / 'backend' / 'data' / 'lingjian.db').as_posix()}",
    )
    redis_url: str = os.getenv("LINGJIAN_REDIS_URL", "redis://127.0.0.1:6379/0")
    redis_cache_db: int = int(os.getenv("LINGJIAN_REDIS_CACHE_DB", "1"))
    redis_cache_url: str = os.getenv(
        "LINGJIAN_REDIS_CACHE_URL",
        f"redis://127.0.0.1:6379/{redis_cache_db}",
    )
    celery_broker_url: str = os.getenv("LINGJIAN_CELERY_BROKER", os.getenv("LINGJIAN_REDIS_URL", "redis://127.0.0.1:6379/0"))
    celery_result_backend: str = os.getenv(
        "LINGJIAN_CELERY_RESULT", os.getenv("LINGJIAN_REDIS_URL", "redis://127.0.0.1:6379/0")
    )
    elasticsearch_url: str = os.getenv("LINGJIAN_ELASTICSEARCH_URL", "")

    jwt_secret: str = os.getenv("LINGJIAN_JWT_SECRET", "change-me-in-production-use-long-random")
    jwt_algorithm: str = os.getenv("LINGJIAN_JWT_ALGORITHM", "HS256")
    jwt_access_expire_minutes: int = int(os.getenv("LINGJIAN_JWT_ACCESS_MINUTES", "60"))
    jwt_refresh_expire_days: int = int(os.getenv("LINGJIAN_JWT_REFRESH_DAYS", "7"))

    log_dir: Path = Path(os.getenv("LINGJIAN_LOG_DIR", str(PROJECT_ROOT / "backend" / "logs")))
    log_level: str = os.getenv("LINGJIAN_LOG_LEVEL", "INFO")
    debug: bool = os.getenv("LINGJIAN_DEBUG", "").lower() in {"1", "true", "yes"}

    rate_limit_per_second: int = int(os.getenv("LINGJIAN_RATE_LIMIT_PER_SECOND", "10"))
    max_upload_bytes: int = int(os.getenv("LINGJIAN_MAX_UPLOAD_BYTES", str(20 * 1024 * 1024)))
    max_text_chars: int = int(os.getenv("LINGJIAN_MAX_TEXT_CHARS", "20000"))

    max_zip_entries: int = int(os.getenv("LINGJIAN_MAX_ZIP_ENTRIES", "200"))
    # 推理结果缓存 TTL（秒）
    cache_infer_ttl_sec: int = int(os.getenv("LINGJIAN_CACHE_INFER_TTL", "86400"))
    cache_session_ttl_sec: int = int(os.getenv("LINGJIAN_CACHE_SESSION_TTL", "86400"))
    # 推理 Redis 缓存命名空间；手动 bump 可一键作废旧缓存（如 LLM/依赖修复后仍命中错误结果）
    infer_cache_version: str = os.getenv("LINGJIAN_INFER_CACHE_VERSION", "").strip()
    # standard_judgment.infer_time 使用的 IANA 时区名
    infer_time_zone: str = os.getenv("LINGJIAN_INFER_TZ", "Asia/Shanghai")
    # 管理端「手动备份」输出目录（SQLite 复制 .db；MySQL 需本机 PATH 有 mysqldump）
    backup_dir: Path = Path(
        os.getenv("LINGJIAN_BACKUP_DIR", str(PROJECT_ROOT / "backend" / "data" / "backups"))
    ).resolve()


settings = Settings()
