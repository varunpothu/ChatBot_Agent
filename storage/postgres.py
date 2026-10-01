from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import json
from uuid import UUID, uuid5, NAMESPACE_URL

from sqlalchemy import create_engine, text

from knowledge.document_registry import ManagedDocument
from ops.runtime import AuditEvent, HumanReviewItem
from rag.models import DocumentChunk, DocumentMetadata, DocumentStatus


def _db_uuid(value: str) -> str:
    """Normalize compact application IDs into canonical PostgreSQL UUID text."""
    try:
        return str(UUID(value))
    except ValueError:
        return str(uuid5(NAMESPACE_URL, value))


class PostgresRuntime:
    """Shared PostgreSQL runtime used by API instances.

    The app keeps the same small interfaces as the local in-memory runtime,
    but data becomes durable and visible to every API instance.
    """

    def __init__(self, database_url: str, auto_init_schema: bool = False):
        if not database_url:
            raise ValueError("DATABASE_URL is required for PostgreSQL runtime")
        self.engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            pool_recycle=1800,
        )
        if auto_init_schema:
            self.init_schema()

    def init_schema(self) -> None:
        schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
        statements = [part.strip() for part in schema.split(";") if part.strip()]
        with self.engine.begin() as conn:
            for statement in statements:
                conn.exec_driver_sql(statement)

    def knowledge_store(self) -> "PostgresKnowledgeStore":
        return PostgresKnowledgeStore(self.engine)

    def document_registry(self) -> "PostgresDocumentRegistry":
        return PostgresDocumentRegistry(self.engine)

    def ops(self) -> "PostgresRuntimeOps":
        return PostgresRuntimeOps(self.engine)


class PostgresKnowledgeStore:
    """Durable knowledge chunks with a monotonic knowledge generation."""

    def __init__(self, engine):
        self.engine = engine

    @property
    def generation(self) -> int:
        with self.engine.connect() as conn:
            value = conn.execute(
                text("SELECT generation FROM knowledge_state WHERE state_id = 1")
            ).scalar_one_or_none()
            return int(value or 0)

    def _bump_generation(self, conn) -> None:
        conn.execute(
            text(
                "UPDATE knowledge_state "
                "SET generation = generation + 1, updated_at = now() "
                "WHERE state_id = 1"
            )
        )

    def add(self, new_chunks: list[DocumentChunk]) -> None:
        if not new_chunks:
            return
        with self.engine.begin() as conn:
            for index, chunk in enumerate(new_chunks):
                embedding = (
                    "[" + ",".join(str(float(x)) for x in chunk.embedding) + "]"
                    if chunk.embedding
                    else None
                )
                conn.execute(
                    text(
                        "INSERT INTO document_chunks "
                        "(chunk_id, document_id, chunk_index, content, page, section, embedding) "
                        "VALUES (:chunk_id, :document_id, :chunk_index, :content, :page, :section, "
                        "CASE WHEN :embedding IS NULL THEN NULL ELSE CAST(:embedding AS vector) END)"
                    ),
                    {
                        "chunk_id": _db_uuid(chunk.chunk_id),
                        "document_id": _db_uuid(chunk.document.document_id),
                        "chunk_index": index,
                        "content": chunk.text,
                        "page": chunk.page,
                        "section": chunk.section,
                        "embedding": embedding,
                    },
                )
            self._bump_generation(conn)

    def set_document_status(self, document_id: str, status: DocumentStatus) -> int:
        with self.engine.begin() as conn:
            result = conn.execute(
                text(
                    "UPDATE documents SET status = :status "
                    "WHERE document_id = CAST(:document_id AS uuid)"
                ),
                {"document_id": _db_uuid(document_id), "status": status.value},
            )
            if result.rowcount:
                self._bump_generation(conn)
            return int(result.rowcount)

    def all(self) -> list[DocumentChunk]:
        with self.engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT c.chunk_id, c.document_id, d.name, d.version, d.category, "
                    "d.status, d.effective_from, d.effective_until, c.page, c.section, "
                    "c.content "
                    "FROM document_chunks c "
                    "JOIN documents d ON d.document_id = c.document_id "
                    "ORDER BY d.name, d.version, c.chunk_index"
                )
            ).mappings().all()

        chunks: list[DocumentChunk] = []
        for row in rows:
            effective_from = row["effective_from"].date() if isinstance(row["effective_from"], datetime) else row["effective_from"]
            effective_until = row["effective_until"].date() if isinstance(row["effective_until"], datetime) else row["effective_until"]
            metadata = DocumentMetadata(
                document_id=str(row["document_id"]),
                name=row["name"],
                version=row["version"],
                category=row["category"],
                status=DocumentStatus(row["status"]),
                effective_from=effective_from,
                effective_until=effective_until,
                access_level="student",
            )
            chunks.append(
                DocumentChunk(
                    chunk_id=str(row["chunk_id"]),
                    document=metadata,
                    page=row["page"],
                    section=row["section"],
                    text=row["content"],
                )
            )
        return chunks


class PostgresDocumentRegistry:
    """Persistent implementation of the governed document lifecycle."""

    def __init__(self, engine):
        self.engine = engine

    def next_version(self, name: str) -> str:
        with self.engine.connect() as conn:
            rows = conn.execute(
                text("SELECT version FROM documents WHERE name = :name"),
                {"name": name},
            ).scalars().all()
        versions: list[int] = []
        for value in rows:
            try:
                versions.append(int(str(value).lstrip("v")))
            except ValueError:
                continue
        return f"v{max(versions, default=0) + 1}"

    def add(self, document: ManagedDocument) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO documents "
                    "(document_id, name, version, content_hash, status, category, owner, source_uri, created_at) "
                    "VALUES (CAST(:document_id AS uuid), :name, :version, :content_hash, "
                    ":status, :category, :owner, :source_uri, :created_at)"
                ),
                {
                    "document_id": document.document_id,
                    "name": document.name,
                    "version": document.version,
                    "content_hash": document.content_hash,
                    "status": document.status,
                    "category": document.category,
                    "owner": None,
                    "source_uri": getattr(document, "source_uri", None),
                    "created_at": document.uploaded_at,
                },
            )

    def get(self, document_id: str) -> ManagedDocument:
        with self.engine.connect() as conn:
            row = conn.execute(
                text(
                    "SELECT document_id, name, version, content_hash, category, status, "
                    "created_at, approved_by, source_uri "
                    "FROM documents WHERE document_id = CAST(:document_id AS uuid)"
                ),
                {"document_id": _db_uuid(document_id)},
            ).mappings().first()
        if row is None:
            raise KeyError("Document not found")
        item = ManagedDocument(
            document_id=str(row["document_id"]),
            name=row["name"],
            version=row["version"],
            content_hash=row["content_hash"],
            category=row["category"],
            status=row["status"],
            uploaded_at=row["created_at"],
            approved_by=row["approved_by"],
        )
        setattr(item, "source_uri", row["source_uri"])
        return item

    def list(self) -> list[ManagedDocument]:
        with self.engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT document_id, name, version, content_hash, category, status, "
                    "created_at, approved_by, source_uri FROM documents ORDER BY created_at DESC"
                )
            ).mappings().all()
        result = []
        for row in rows:
            item = ManagedDocument(
                document_id=str(row["document_id"]),
                name=row["name"],
                version=row["version"],
                content_hash=row["content_hash"],
                category=row["category"],
                status=row["status"],
                uploaded_at=row["created_at"],
                approved_by=row["approved_by"],
            )
            setattr(item, "source_uri", row["source_uri"])
            result.append(item)
        return result

    def counts(self) -> dict[str, int]:
        with self.engine.connect() as conn:
            rows = conn.execute(
                text("SELECT status, COUNT(*) AS count FROM documents GROUP BY status")
            ).all()
        return {str(status): int(count) for status, count in rows}

    def activate(self, document_id: str, approved_by: str) -> list[str]:
        with self.engine.begin() as conn:
            target = conn.execute(
                text(
                    "SELECT name, status FROM documents "
                    "WHERE document_id = CAST(:document_id AS uuid) FOR UPDATE"
                ),
                {"document_id": document_id},
            ).mappings().first()
            if target is None:
                raise KeyError("Document not found")
            if target["status"] not in {"PENDING_REVIEW", "APPROVED"}:
                raise ValueError("Document must be APPROVED or PENDING_REVIEW before activation")

            archived = conn.execute(
                text(
                    "UPDATE documents SET status = 'ARCHIVED' "
                    "WHERE name = :name AND status = 'ACTIVE' "
                    "RETURNING document_id"
                ),
                {"name": target["name"]},
            ).scalars().all()

            conn.execute(
                text(
                    "UPDATE documents SET status = 'ACTIVE', approved_by = :approved_by "
                    "WHERE document_id = CAST(:document_id AS uuid)"
                ),
                {"document_id": _db_uuid(document_id), "approved_by": approved_by},
            )
            conn.execute(
                text(
                    "UPDATE knowledge_state SET generation = generation + 1, updated_at = now() "
                    "WHERE state_id = 1"
                )
            )
            return [str(item) for item in archived]

    def set_status(self, document_id: str, status: str) -> None:
        with self.engine.begin() as conn:
            result = conn.execute(
                text(
                    "UPDATE documents SET status = :status "
                    "WHERE document_id = CAST(:document_id AS uuid)"
                ),
                {"document_id": _db_uuid(document_id), "status": status},
            )
            if not result.rowcount:
                raise KeyError("Document not found")
            self._bump_generation(conn)

    def reject(self, document_id: str, reviewer: str) -> None:
        with self.engine.begin() as conn:
            result = conn.execute(
                text(
                    "UPDATE documents SET status = 'REJECTED', approved_by = :reviewer "
                    "WHERE document_id = CAST(:document_id AS uuid) AND status = 'PENDING_REVIEW'"
                ),
                {"document_id": _db_uuid(document_id), "reviewer": reviewer},
            )
            if not result.rowcount:
                raise ValueError("Only pending-review documents can be rejected")
            conn.execute(
                text(
                    "UPDATE knowledge_state SET generation = generation + 1, updated_at = now() "
                    "WHERE state_id = 1"
                )
            )


class PostgresRuntimeOps:
    """Durable audit and human-review queue."""

    def __init__(self, engine):
        self.engine = engine

    def audit(self, event_type: str, actor: str, subject_id: str | None, details: dict) -> AuditEvent:
        from datetime import timezone
        from uuid import uuid4

        event_id = uuid4().hex
        created_at = datetime.now(timezone.utc).isoformat()
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO audit_events "
                    "(event_id, event_type, actor, subject_id, details, created_at) "
                    "VALUES (CAST(:event_id AS uuid), :event_type, :actor, :subject_id, "
                    "CAST(:details AS jsonb), :created_at)"
                ),
                {
                    "event_id": event_id,
                    "event_type": event_type,
                    "actor": actor,
                    "subject_id": subject_id,
                    "details": json.dumps(details),
                    "created_at": created_at,
                },
            )
        return AuditEvent(event_id, event_type, actor, subject_id, details, created_at)

    def enqueue_review(self, reason: str, message: str, conversation_id: str | None) -> HumanReviewItem:
        from uuid import uuid4

        review_id = uuid4().hex
        created_at = datetime.now().astimezone().isoformat()
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO human_review_queue "
                    "(review_id, conversation_id, reason, message, created_at) "
                    "VALUES (CAST(:review_id AS uuid), "
                    "CASE WHEN :conversation_id IS NULL THEN NULL ELSE CAST(:conversation_id AS uuid) END, "
                    ":reason, :message, :created_at)"
                ),
                {
                    "review_id": review_id,
                    "conversation_id": conversation_id,
                    "reason": reason,
                    "message": message,
                    "created_at": created_at,
                },
            )
        return HumanReviewItem(review_id, reason, message, conversation_id, created_at=created_at)

    def list_reviews(self, status: str | None = None) -> list[HumanReviewItem]:
        clause = " WHERE status = :status" if status else ""
        params = {"status": status} if status else {}
        with self.engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT review_id, reason, message, conversation_id, status, "
                    "created_at, resolved_by, resolution FROM human_review_queue"
                    + clause
                    + " ORDER BY created_at DESC"
                ),
                params,
            ).mappings().all()
        return [
            HumanReviewItem(
                str(row["review_id"]),
                row["reason"],
                row["message"],
                str(row["conversation_id"]) if row["conversation_id"] else None,
                row["status"],
                row["created_at"].isoformat() if hasattr(row["created_at"], "isoformat") else str(row["created_at"]),
                row["resolved_by"],
                row["resolution"],
            )
            for row in rows
        ]

    def resolve_review(self, review_id: str, reviewer: str, resolution: str) -> HumanReviewItem:
        with self.engine.begin() as conn:
            row = conn.execute(
                text(
                    "UPDATE human_review_queue SET status='RESOLVED', resolved_by=:reviewer, "
                    "resolution=:resolution, resolved_at=now() "
                    "WHERE review_id=CAST(:review_id AS uuid) "
                    "RETURNING review_id, reason, message, conversation_id, status, created_at, resolved_by, resolution"
                ),
                {"review_id": _db_uuid(review_id), "reviewer": reviewer, "resolution": resolution},
            ).mappings().first()
            if row is None:
                raise KeyError("Review not found")
        return HumanReviewItem(
            str(row["review_id"]),
            row["reason"],
            row["message"],
            str(row["conversation_id"]) if row["conversation_id"] else None,
            row["status"],
            row["created_at"].isoformat() if hasattr(row["created_at"], "isoformat") else str(row["created_at"]),
            row["resolved_by"],
            row["resolution"],
        )

    def list_audit(self, limit: int = 200) -> list[AuditEvent]:
        limit = max(1, min(limit, 1000))
        with self.engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT event_id, event_type, actor, subject_id, details, created_at "
                    "FROM audit_events ORDER BY created_at DESC LIMIT :limit"
                ),
                {"limit": limit},
            ).mappings().all()
        return [
            AuditEvent(
                str(row["event_id"]),
                row["event_type"],
                row["actor"],
                row["subject_id"],
                row["details"] or {},
                row["created_at"].isoformat() if hasattr(row["created_at"], "isoformat") else str(row["created_at"]),
            )
            for row in rows
        ]
