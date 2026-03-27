from src.plugins.alconna.uniseg.constraint import SupportAdapter
from src.plugins.alconna.uniseg.loader import BaseLoader


class Loader(BaseLoader):
    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.console

    def get_builder(self):
        from .builder import ConsoleMessageBuilder

        return ConsoleMessageBuilder()

    def get_exporter(self):
        from .exporter import ConsoleMessageExporter

        return ConsoleMessageExporter()
