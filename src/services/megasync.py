import json
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterable, IO

import mega

from src.data import FullItem
from src.enums import ServiceType
from src.models.post import PostRecord
from src.services import PushService

@dataclass
class MegaConfig:
    username: str
    password: str
    root: str


class MegaService(PushService):
    def __init__(self, config: MegaConfig):
        self.client = mega.Mega()
        self.client.login(config.username, config.password)
        self.root = Path(config.root)

    def write_file(self, path: Path, buffer: IO):
        with NamedTemporaryFile() as f:
            f.write(buffer.read())
            f.flush()
            folder = self.client.find(str(path.parent))
            self.client.upload(f.name, folder[0], str(path.name))

    def push_item(self, item: FullItem, images: Iterable[IO], channel: str):
        d = self.root / item.service.value() / item.source_id
        self.client.create_folder(str(d))
        json_buffer = BytesIO(json.dumps(item.to_dict(), ensure_ascii=False).encode('utf-8'))
        json_fp = d / f"{item.item_id}_info.json"
        self.write_file(json_fp, json_buffer)
        PostRecord.put_record(item.service, item.item_id, ServiceType.WebDav, json_fp, channel)

        for idx, img in enumerate(images):
            fp = d / f"{item.item_id}_{idx:03d}.png"
            self.write_file(fp, img)
            PostRecord.put_record(item.service, item.item_id, ServiceType.WebDav, fp, channel)



