from typing import TYPE_CHECKING, Union

from nonebot.adapters import Bot
from nonebot.adapters.mirai.bot import Bot as MiraiBot

from src.plugins.alconna.uniseg.constraint import SupportAdapter
from src.plugins.alconna.uniseg.target import Target, TargetFetcher


class MiraiTargetFetcher(TargetFetcher):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.mirai

    async def fetch(self, bot: Bot, target: Union[Target, None] = None):
        if TYPE_CHECKING:
            assert isinstance(bot, MiraiBot)
        if target and target.channel:
            return
        if not target or not target.private:
            groups = await bot.get_group_list()
            for group in groups:
                yield Target(
                    str(group.id),
                    adapter=self.get_adapter(),
                    self_id=bot.self_id,
                )
        if not target or target.private:
            friends = await bot.get_friend_list()
            for friend in friends:
                yield Target(
                    str(friend.id),
                    private=True,
                    adapter=self.get_adapter(),
                    self_id=bot.self_id,
                )
