import re
from abc import ABC, abstractmethod
from typing import Union, Iterable, IO, Optional

from src.data import IndexItem, FullItem


class SubscribeService(ABC):
    @abstractmethod
    def subscribe_index(self, name: str) -> Iterable[IndexItem]:
        pass

    @abstractmethod
    def subscribe_full(self, name: str) -> Iterable[FullItem]:
        pass

    @classmethod
    @abstractmethod
    def get_title(cls, name: str) -> Optional[str]:
        pass

    @classmethod
    @abstractmethod
    def get_url(cls, name: str) -> Optional[str]:
        pass


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


class PushService(ABC):
    @abstractmethod
    def push_item(self, item: FullItem, images: Iterable[IO], channel: str):
        pass


BaseService = Union[SubscribeService, PullService, PushService]
