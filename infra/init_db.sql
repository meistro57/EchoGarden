CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS conversations (
  conv_id       TEXT PRIMARY KEY,
  title         TEXT,
  owner_id      TEXT NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  checksum      TEXT,                 -- rolling checksum over messages
  meta          JSONB
);

-- messages
CREATE TABLE IF NOT EXISTS messages (
  conv_id       TEXT REFERENCES conversations(conv_id) ON DELETE CASCADE,
  msg_id        TEXT,
  role          TEXT CHECK (role IN ('user','assistant','system','tool')),
  ts            TIMESTAMPTZ NOT NULL,
  text          TEXT NOT NULL,
  parent_id     TEXT,
  hash          TEXT,                 -- sha256(text canonical)
  meta          JSONB,
  PRIMARY KEY (conv_id, msg_id)
);
CREATE INDEX IF NOT EXISTS idx_messages_ts        ON messages(ts);
CREATE INDEX IF NOT EXISTS idx_messages_text_gin  ON messages USING GIN (to_tsvector('english', text));

-- tags (freeform labels)
CREATE TABLE IF NOT EXISTS message_tags (
  conv_id   TEXT,
  msg_id    TEXT,
  tag       TEXT,
  PRIMARY KEY (conv_id, msg_id, tag),
  FOREIGN KEY (conv_id, msg_id) REFERENCES messages(conv_id, msg_id) ON DELETE CASCADE
);

-- embeddings (pgvector or external ANN)
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS message_embeddings (
  conv_id   TEXT,
  msg_id    TEXT,
  embedding VECTOR(1536),
  model     TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (conv_id, msg_id),
  FOREIGN KEY (conv_id, msg_id) REFERENCES messages(conv_id, msg_id) ON DELETE CASCADE
);

-- entities/sentiment/topics
CREATE TABLE IF NOT EXISTS message_analytics (
  conv_id   TEXT,
  msg_id    TEXT,
  sentiment NUMERIC,
  entities  JSONB,
  topics    TEXT[],
  PRIMARY KEY (conv_id, msg_id),
  FOREIGN KEY (conv_id, msg_id) REFERENCES messages(conv_id, msg_id) ON DELETE CASCADE
);