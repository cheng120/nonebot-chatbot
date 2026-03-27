from src.plugins.alconna.uniseg.constraint import SupportAdapter
from src.plugins.alconna.uniseg.loader import BaseLoader


class Loader(BaseLoader):
    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.tail_chat

    def get_builder(self):
        from .builder import TailChatMessageBuilder

        return TailChatMessageBuilder()

    def get_exporter(self):
        from .exporter import TailChatMessageExporter

        return TailChatMessageExporter()

    def get_fetcher(self):
        from .target import TailChatTargetFetcher

        return TailChatTargetFetcher()
