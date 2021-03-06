from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from src.enums import ServiceType


@dataclass
class FullItem:
    service: ServiceType
    item_id: str
    source_id: str
    content: str
    image_urls: List[str]
    url: str

    def to_dict(self):
        return {
            'service': self.service.value,
            'item_id': self.item_id,
            'source_id': self.source_id,
            'content': self.content,
            'image_urls': self.image_urls,
            'url': self.url
        }


@dataclass
class IndexItem:
    service: ServiceType
    item_id: str
