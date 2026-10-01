CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS knowledge_state (
    state_id INTEGER PRIMARY KEY CHECK (state_id = 1),
    generation BIGINT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO knowledge_state (state_id, generation)
VALUES (1, 0)
ON CONFLICT (state_id) DO NOTHING;

CREATE TABLE IF NOT EXISTS documents (
    document_id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    source_uri TEXT,
    status TEXT NOT NULL CHECK (status IN ('DRAFT','PROCESSING','PENDING_REVIEW','APPROVED','ACTIVE','ARCHIVED','REJECTED')),
    category TEXT NOT NULL,
    effective_from TIMESTAMPTZ,
    effective_until TIMESTAMPTZ,
    owner TEXT,
    approved_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(name, version),
    UNIQUE(content_hash)
);

CREATE TABLE IF NOT EXISTS document_chunks (
    chunk_id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(document_id),
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    page INTEGER,
    section TEXT,
    embedding vector(512),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chunks_document ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_content_fts
    ON document_chunks USING GIN (to_tsvector('simple', content));
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw
    ON document_chunks USING hnsw (embedding vector_cosine_ops)
    WHERE embedding IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_documents_active ON documents(status, name);
CREATE INDEX IF NOT EXISTS idx_documents_effective ON documents(effective_from, effective_until);

CREATE TABLE IF NOT EXISTS conversations (
    conversation_id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_intent TEXT
);

CREATE TABLE IF NOT EXISTS conversation_state (
    conversation_id UUID PRIMARY KEY REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    last_query TEXT NOT NULL,
    last_intent TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS conversation_turns (
    turn_id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES conversations(conversation_id),
    user_text TEXT NOT NULL,
    assistant_text TEXT NOT NULL,
    grounded BOOLEAN NOT NULL,
    citations_count INTEGER NOT NULL DEFAULT 0,
    latency_ms DOUBLE PRECISION NOT NULL DEFAULT 0,
    model_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_turns_conversation ON conversation_turns(conversation_id, created_at);

CREATE TABLE IF NOT EXISTS audit_events (
    event_id UUID PRIMARY KEY,
    event_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    subject_id TEXT,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_events(created_at DESC);

CREATE TABLE IF NOT EXISTS human_review_queue (
    review_id UUID PRIMARY KEY,
    conversation_id UUID,
    reason TEXT NOT NULL,
    message TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN','RESOLVED')),
    resolved_by TEXT,
    resolution TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS model_registry (
    model_key TEXT NOT NULL,
    version TEXT NOT NULL,
    provider TEXT NOT NULL,
    model_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('DRAFT','PENDING_REVIEW','APPROVED','ACTIVE','REJECTED','ARCHIVED')),
    configuration JSONB NOT NULL DEFAULT '{}'::jsonb,
    owner TEXT,
    approved_by TEXT,
    approved_at TIMESTAMPTZ,
    evaluation_reference TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (model_key, version)
);

CREATE INDEX IF NOT EXISTS idx_model_registry_active
    ON model_registry(model_key, status);

CREATE TABLE IF NOT EXISTS prompt_registry (
    prompt_key TEXT NOT NULL,
    version TEXT NOT NULL,
    prompt_hash TEXT NOT NULL,
    template TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('DRAFT','PENDING_REVIEW','APPROVED','ACTIVE','REJECTED','ARCHIVED')),
    owner TEXT,
    approved_by TEXT,
    approved_at TIMESTAMPTZ,
    evaluation_reference TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (prompt_key, version),
    UNIQUE(prompt_key, prompt_hash)
);

CREATE INDEX IF NOT EXISTS idx_prompt_registry_active
    ON prompt_registry(prompt_key, status);

ALTER TABLE model_registry ADD COLUMN IF NOT EXISTS evaluation_reference TEXT;
ALTER TABLE prompt_registry ADD COLUMN IF NOT EXISTS evaluation_reference TEXT;
