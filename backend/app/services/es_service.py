"""Elasticsearch：可选启用；索引与检索。"""
from __future__ import annotations

import logging
from typing import Any

from backend.app.core.config import settings

logger = logging.getLogger("backend.app.es")

INDEX_NAME = "lingjian-contents"


class EsService:
    def __init__(self) -> None:
        self._client: Any = None
        url = (settings.elasticsearch_url or "").strip()
        if url:
            try:
                from elasticsearch import Elasticsearch

                self._client = Elasticsearch(url)
                logger.info("Elasticsearch client initialized")
            except Exception as e:
                logger.warning("Elasticsearch disabled: %s", e)
                self._client = None

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def ensure_index(self) -> None:
        if not self._client:
            return
        if self._client.indices.exists(index=INDEX_NAME):
            return
        self._client.indices.create(
            index=INDEX_NAME,
            mappings={
                "properties": {
                    "content_id": {"type": "keyword"},
                    "owner_id": {"type": "integer"},
                    "text": {"type": "text"},
                    "risk_level": {"type": "keyword"},
                    "features": {"type": "keyword"},
                }
            },
        )

    def index_content(self, doc_id: str, doc: dict[str, Any]) -> None:
        if not self._client:
            return
        try:
            self.ensure_index()
            self._client.index(index=INDEX_NAME, id=doc_id, document=doc)
        except Exception as e:
            logger.warning("ES index failed: %s", e)

    def search_for_user(
        self,
        *,
        owner_id: int,
        q: str,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        if not self._client:
            raise RuntimeError("Elasticsearch 未配置")
        self.ensure_index()
        from_ = max(0, (page - 1) * page_size)
        body = {
            "bool": {
                "must": [{"match": {"text": {"query": q}}}],
                "filter": [{"term": {"owner_id": owner_id}}],
            }
        }
        resp = self._client.search(
            index=INDEX_NAME,
            query=body,
            highlight={
                "fields": {"text": {"pre_tags": ["<em>"], "post_tags": ["</em>"]}},
                "require_field_match": False,
            },
            from_=from_,
            size=page_size,
        )
        hits = resp.get("hits", {})
        items = []
        for h in hits.get("hits", []):
            src = h.get("_source", {})
            hl = h.get("highlight", {}).get("text")
            items.append(
                {
                    "content_id": src.get("content_id"),
                    "risk_level": src.get("risk_level"),
                    "highlight": hl,
                    "text": src.get("text"),
                }
            )
        total = hits.get("total", {})
        if isinstance(total, dict):
            total_val = total.get("value", 0)
        else:
            total_val = total
        return {"items": items, "total": total_val}


es_service = EsService()
