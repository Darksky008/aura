import uuid

from sqlalchemy import JSON, Boolean, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base
from app.models.base import TimestampMixin, uuid_pk

DOC_TYPES = ("restaurant", "chef", "philosophy", "faq", "policy", "dish_story", "preparation")


class KnowledgeDocument(Base, TimestampMixin):
    """Free-text hotel knowledge. To add semantic search later: add an `embedding vector(N)` column
    (pgvector) and implement `VectorBackend` in services/knowledge/service.py - no other code changes."""

    __tablename__ = "knowledge_documents"

    id: Mapped[uuid.UUID] = uuid_pk()
    hotel_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("hotels.id", ondelete="CASCADE"), index=True)
    restaurant_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("restaurants.id", ondelete="CASCADE"))
    doc_type: Mapped[str] = mapped_column(String(30), default="faq")
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
