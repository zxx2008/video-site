CREATE TABLE IF NOT EXISTS videos (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    title         TEXT    NOT NULL,
    filename      TEXT    NOT NULL,
    storage_path  TEXT    NOT NULL,
    thumbnail_path TEXT   DEFAULT NULL,
    mime_type     TEXT    NOT NULL,
    file_size     INTEGER NOT NULL,
    duration      REAL    DEFAULT 0,
    resolution    TEXT    DEFAULT '',
    codec         TEXT    DEFAULT '',
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos(created_at DESC);
