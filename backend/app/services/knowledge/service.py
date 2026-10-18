"""KnowledgeService: one interface for search/retrieve, swappable backends.

  * PgFullTextBackend  - PostgreSQL full-text search (default on Postgres)
  * KeywordBackend     - portable fallback (SQLite/tests)
  * VectorBackend      - documented extension point for pgvector (embedding -> cosine search)
"""
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.text import tokens
from app.models import KnowledgeDocument


@dataclass
class Passage:
    id: str
    title: str
    doc_type: str
    content: str
    score: float


class SearchBackend(ABC):
    @abstractmethod
    def search(self, db: Session, hotel_id: uuid.UUID, query: str, doc_types: list[str] | None, limit: int) -> list[Passage]: ...


def _base(hotel_id, doc_types):
    q = select(KnowledgeDocument).where(KnowledgeDocument.hotel_id == hotel_id, KnowledgeDocument.is_published.is_(True))
    if doc_types:
        q = q.where(KnowledgeDocument.doc_type.in_(doc_types))
    return q


class KeywordBackend(SearchBackend):
    def search(self, db, hotel_id, query, doc_types, limit):
        qt = set(tokens(query))
        out = []
        for doc in db.scalars(_base(hotel_id, doc_types)):
            title_t, body_t = set(tokens(doc.title)), tokens(doc.content)
            score = 3 * len(qt & title_t) + sum(1 for t in body_t if t in qt) / (1 + len(body_t) ** 0.5)
            if score > 0:
                out.append(Passage(str(doc.id), doc.title, doc.doc_type, doc.content, round(score, 3)))
        return sorted(out, key=lambda p: -p.score)[:limit]


class PgFullTextBackend(SearchBackend):
    def search(self, db, hotel_id, query, doc_types, limit):
        vec = func.to_tsvector("simple", KnowledgeDocument.title + " " + KnowledgeDocument.content)
        ts = func.plainto_tsquery("simple", query)
        rank = func.ts_rank(vec, ts)
        q = _base(hotel_id, doc_types).where(vec.op("@@")(ts)).add_columns(rank).order_by(rank.desc()).limit(limit)
        rows = db.execute(q).all()
        if not rows:  # plainto_tsquery ANDs terms; fall back to forgiving keyword scoring
            return KeywordBackend().search(db, hotel_id, query, doc_types, limit)
        return [Passage(str(d.id), d.title, d.doc_type, d.content, float(r)) for d, r in rows]


class VectorBackend(SearchBackend):  # pragma: no cover - extension point
    """Future: embed(query) -> `ORDER BY embedding <=> :q LIMIT n` using pgvector."""

    def search(self, db, hotel_id, query, doc_types, limit):
        raise NotImplementedError("Add a pgvector column + embedding provider, then implement this.")


class KnowledgeService:
    def __init__(self, db: Session, hotel_id: uuid.UUID, backend: SearchBackend | None = None):
        self.db, self.hotel_id = db, hotel_id
        if backend is None:
            backend = PgFullTextBackend() if db.get_bind().dialect.name == "postgresql" else KeywordBackend()
        self.backend = backend

    def search(self, query: str, *, doc_types: list[str] | None = None, limit: int = 3) -> list[Passage]:
        return self.backend.search(self.db, self.hotel_id, query, doc_types, limit)

    def retrieve(self, doc_id: uuid.UUID) -> KnowledgeDocument | None:
        doc = self.db.get(KnowledgeDocument, doc_id)
        return doc if doc and doc.hotel_id == self.hotel_id else None
