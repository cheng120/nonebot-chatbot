from nonebot.adapters import MessageSegment

from src.plugins.alconna.uniseg.builder import MessageBuilder, build
from src.plugins.alconna.uniseg.constraint import SupportAdapter
from src.plugins.alconna.uniseg.segment import Text


class NonebugMessageBuilder(MessageBuilder):
    @classmethod
    def get_adapter(cls) -> SupportAdapter:
        return SupportAdapter.nonebug

    @build("text")
    def text(self, seg: MessageSegment):
        return Text(seg.data["text"])
