import aiosqlite
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = Path("/mnt/mydisk/video-site/videohub.db")
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


async def init_db():
    """应用启动时执行建表语句"""
    async with aiosqlite.connect(DB_PATH) as db:
        schema = SCHEMA_PATH.read_text()
        await db.executescript(schema)
        await _migrate_videos_table(db)
        await db.commit()


async def _migrate_videos_table(db: aiosqlite.Connection):
    """为历史数据库补齐新增字段"""
    cursor = await db.execute("PRAGMA table_info(videos)")
    rows = await cursor.fetchall()
    existing_columns = {row[1] for row in rows}

    required_columns = {
        "playback_path": "TEXT DEFAULT NULL",
        "sample_aspect_ratio": "TEXT DEFAULT ''",
        "display_aspect_ratio": "TEXT DEFAULT ''",
    }

    for column_name, column_type in required_columns.items():
        if column_name not in existing_columns:
            await db.execute(f"ALTER TABLE videos ADD COLUMN {column_name} {column_type}")


async def get_db():
    """获取数据库连接（异步上下文管理器）"""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()
