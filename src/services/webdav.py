import json
from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO
from tempfile import TemporaryFile, NamedTemporaryFile
from typing import Iterable, IO

from webdav3.client import Client

from src.data import FullItem
from src.enums import ServiceType
from src.models.post import PostRecord
from src.models.user import UserInfo
from src.services.base import PushService


@dataclass
class WebDavConfig:
    host: str
    port: int
    use_https: bool
    username: str
    password: str
    path: str
    root_dir: str


class WebDavServiceBase:
    def __init__(self, conf: WebDavConfig):
        url = f"http{'s' if conf.use_https else ''}://{conf.host}:{conf.port}{conf.path}{conf.root_dir}"
        options = {
            'webdav_hostname': url,
            'webdav_login': conf.username,
            'webdav_password': conf.password
        }
        self.client = Client(options)
        self.dir_struct = {}
        from src.services import pull_services
        for t in pull_services.keys():
            if self.client.check(t.value):
                self.dir_struct[t] = set(x[:-1] for x in self.client.list(t.value)) - {t.value}
            else:
                self.dir_struct[t] = set()
                self.client.mkdir(t.value)

    def write_file(self, service: ServiceType, dir_name: str, filename: str, buffer: IO):
        if dir_name not in self.dir_struct[service]:
            self.client.mkdir(f"{service.value}/{dir_name}")
            self.dir_struct[service].add(dir_name)
        fp = f"{service.value}/{dir_name}/{filename}"
        with NamedTemporaryFile() as f:
            f.write(buffer.read())
            f.flush()
            self.client.upload(fp, f.name)
        return fp


class WebDavService(PushService, WebDavServiceBase):
    def push_item(self, item: FullItem, images: Iterable[IO], channel: str):
        json_buffer = BytesIO(json.dumps(item.to_dict(), ensure_ascii=False).encode('utf-8'))
        # nickname = UserInfo.get_nickname(item.service, item.source_id)
        # if nickname is None:
        #     dir_name = f"({item.source_id})"
        # else:
        #     dir_name = f"{nickname}({item.source_id})"
        dir_name = item.source_id
        fp = self.write_file(item.service, dir_name, f"{item.item_id}_info.json", json_buffer)
        PostRecord.put_record(item.service, item.item_id, ServiceType.WebDav, fp, channel)

        for idx, img in enumerate(images):
            fp = self.write_file(item.service, dir_name, f"{item.item_id}_{idx:03d}.png", img)
            PostRecord.put_record(item.service, item.item_id, ServiceType.WebDav, fp, channel)
