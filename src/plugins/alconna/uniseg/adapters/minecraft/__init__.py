from src.plugins.alconna.uniseg.constraint import SupportAdapter
from src.plugins.alconna.uniseg.loader import BaseLoader


class Loader(BaseLoader):
    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.minecraft

    def get_builder(self):
        from .builder import MinecraftMessageBuilder

        return MinecraftMessageBuilder()

    def get_exporter(self):
        from .exporter import MinecraftMessageExporter

        return MinecraftMessageExporter()
