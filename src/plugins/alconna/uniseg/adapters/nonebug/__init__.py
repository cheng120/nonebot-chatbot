from src.plugins.alconna.uniseg.constraint import SupportAdapter
from src.plugins.alconna.uniseg.loader import BaseLoader


class Loader(BaseLoader):
    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.nonebug

    def get_builder(self):
        from .builder import NonebugMessageBuilder

        return NonebugMessageBuilder()

    def get_exporter(self):
        from .exporter import NonebugMessageExporter

        return NonebugMessageExporter()
