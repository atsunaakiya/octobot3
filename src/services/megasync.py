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
        self.dir_cache = {}

    def ensure_dir(self, path: Path):
        if path in self.dir_cache:
            return self.dir_cache[path]
        sp = str(path)
        folder = self.client.find(sp)
        if folder is None:
            folder = self.client.create_folder(sp)[path.name]
        else:
            folder = folder[0]
        self.dir_cache[path] = folder
        return folder

    def write_file(self, path: Path, buffer: IO):
        with NamedTemporaryFile() as f:
            f.write(buffer.read())
            f.flush()
            folder = self.ensure_dir(path.parent)
            self.client.upload(f.name, folder[0], str(path.name))

    def push_item(self, item: FullItem, images: Iterable[IO], channel: str):
        d = self.root / item.service.value / item.source_id
        self.ensure_dir(d)
        json_buffer = BytesIO(json.dumps(item.to_dict(), ensure_ascii=False).encode('utf-8'))
        json_fp = d / f"{item.item_id}_info.json"
        self.write_file(json_fp, json_buffer)
        PostRecord.put_record(item.service, item.item_id, ServiceType.Mega, json_fp, channel)

        for idx, img in enumerate(images):
            fp = d / f"{item.item_id}_{idx:03d}.png"
            self.write_file(fp, img)
            PostRecord.put_record(item.service, item.item_id, ServiceType.Mega, fp, channel)



