import re
from abc import ABC, abstractmethod
from typing import Union, Iterable, IO, Optional, List

from src.data import IndexItem, FullItem


class SubscribeService(ABC):
    @abstractmethod
    def subscribe_index(self, name: str) -> Iterable[IndexItem]:
        return []

    @abstractmethod
    def subscribe_full(self, name: str) -> Iterable[FullItem]:
        return []

    @classmethod
    @abstractmethod
    def get_title(cls, name: str) -> Optional[str]:
        pass

    @classmethod
    @abstractmethod
    def get_url(cls, name: str) -> Optional[str]:
        pass

    @classmethod
    def options(cls) -> Optional[List[str]]:
        return None


class PullService(ABC):
    @abstractmethod
    def pull_item(self, index_item: IndexItem) -> FullItem:
        pass

    @abstractmethod
    def download_item_image(self, item: FullItem, url: str) -> IO:
        pass

    @classmethod
    @abstractmethod
    def parse_item_id(cls, url) -> Optional[str]:
        pass

    @classmethod
    def convert_username(cls, name: str):
        return name


class PushService(ABC):
    @abstractmethod
    def push_item(self, item: FullItem, images: Iterable[IO], channel: str, converted_username: str):
        pass


BaseService = Union[SubscribeService, PullService, PushService]
