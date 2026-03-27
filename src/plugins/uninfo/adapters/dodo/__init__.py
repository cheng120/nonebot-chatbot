from src.plugins.uninfo.constraint import SupportAdapter
from src.plugins.uninfo.fetch import InfoFetcher
from src.plugins.uninfo.loader import BaseLoader


class Loader(BaseLoader):
    def get_adapter(self) -> SupportAdapter:
        return SupportAdapter.dodo

    def get_fetcher(self) -> InfoFetcher:
        from .main import fetcher

        return fetcher
