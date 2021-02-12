import json
import threading
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
from src.models.utils import ServiceKVStore
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

SERVICE_NAME='webdav.post.service'

class WebDavServiceBase:
    def __init__(self, conf: WebDavConfig):
        url = f"http{'s' if conf.use_https else ''}://{conf.host}:{conf.port}{conf.path}{conf.root_dir}"
        options = {
            'webdav_hostname': url,
            'webdav_login': conf.username,
            'webdav_password': conf.password,
            'webdav_timeout': 600
        }
        self.client = Client(options)
        self.sem = threading.Semaphore(5)

    def ensure_dir(self, path: str):
        if ServiceKVStore.exists(SERVICE_NAME, path):
            return
        if self.client.check(path):
            ServiceKVStore.put(SERVICE_NAME, path, {})
            return
        self.client.mkdir(path)
        ServiceKVStore.put(SERVICE_NAME, path, {})

    def write_file(self, service: ServiceType, dir_name: str, filename: str, buffer: IO):
        with self.sem:
            self.ensure_dir(service.value)
            self.ensure_dir(f"{service.value}/{dir_name}")
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
