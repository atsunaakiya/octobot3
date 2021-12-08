import json
from dataclasses import dataclass
from typing import Iterable, IO

from pathlib import Path

from src.data import FullItem
from src.services import PushService


@dataclass
class LocalConfig:
    root: str = '/external'


class LocalService(PushService):
    def __init__(self, config: LocalConfig):
        self.config = LocalConfig
        self.root = Path(config.root)

    def push_item(self, item: FullItem, images: Iterable[IO], channel: str, converted_username: str):
        parent = self.root / item.service.value / converted_username
        parent.mkdir(parents=True, exist_ok=True)
        meta_file = parent / f"{item.item_id}_info.json"
        json.dump(item.to_dict(), meta_file.open('w'), ensure_ascii=False)
        for idx, buf in enumerate(images):
            fp = parent / f"{item.item_id}_{idx:03d}.png"
            with fp.open('wb') as f:
                f.write(buf.read())
