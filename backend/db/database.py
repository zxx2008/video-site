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
        await db.commit()


async def get_db():
    """获取数据库连接（异步上下文管理器）"""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()
