from typing import Optional

from nonebot_plugin_orm import get_session
from sqlalchemy import select

from .model import ShindanConfig, ShindanRecord


class ShindanManager:
    def __init__(self):
        self.shindan_list: list[ShindanConfig] = []

    async def load_shindan(self):
        async with get_session() as session:
            statement = select(ShindanRecord)
            shindan_records = (await session.scalars(statement)).all()
            self.shindan_list = [record.config for record in shindan_records]

    async def add_shindan(self, id: int, command: str, title: str, mode: str = "image"):
        async with get_session() as session:
            record = ShindanRecord(
                shindan_id=id, command=command, title=title, mode=mode
            )
            session.add(record)
            await session.commit()
        await self.load_shindan()

    async def remove_shindan(self, id: int):
        async with get_session() as session:
            statement = select(ShindanRecord).where(ShindanRecord.shindan_id == id)
            if record := await session.scalar(statement):
                await session.delete(record)
                await session.commit()
        await self.load_shindan()

    async def set_shindan(
        self,
        id: int,
        *,
        command: Optional[str] = None,
        title: Optional[str] = None,
        mode: Optional[str] = None,
    ):
        async with get_session() as session:
            statement = select(ShindanRecord).where(ShindanRecord.shindan_id == id)
            if record := await session.scalar(statement):
                if command:
                    record.command = command
                if title:
                    record.title = title
                if mode:
                    record.mode = mode
                session.add(record)
                await session.commit()
        await self.load_shindan()


# 默认占卜列表（与迁移中的默认数据一致，表为空时初始化）
DEFAULT_SHINDAN_RECORDS = [
    (162207, "今天是什么少女", "你的二次元少女化形象", "image"),
    (917962, "人设生成", "人设生成器", "image"),
    (790697, "中二称号", "奇妙的中二称号生成器", "image"),
    (587874, "异世界转生", "異世界轉生—∩開始的種族∩——", "image"),
    (940824, "魔法人生", "魔法人生：我在霍格沃兹读书时发生的两三事", "image"),
    (1075116, "抽老婆", "あなたの二次元での嫁ヒロイン", "text"),
    (400813, "抽舰娘", "【艦これ】あなたの嫁になる艦娘は？", "image"),
    (361845, "抽高达", "マイ・ガンダム診断", "image"),
    (595068, "英灵召唤", "Fate 英霊召喚", "image"),
    (360578, "卖萌", "顔文字作るよ(  ﾟдﾟ )", "text"),
]


async def init_default_shindan_if_empty():
    """若占卜表为空则写入默认占卜，保证「魔法人生」等命令可用"""
    async with get_session() as session:
        statement = select(ShindanRecord)
        existing = (await session.scalars(statement)).first()
    if existing is not None:
        return
    for shindan_id, command, title, mode in DEFAULT_SHINDAN_RECORDS:
        async with get_session() as session:
            session.add(
                ShindanRecord(
                    shindan_id=shindan_id,
                    command=command,
                    title=title,
                    mode=mode,
                )
            )
            await session.commit()


shindan_manager = ShindanManager()
