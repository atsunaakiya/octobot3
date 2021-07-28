import json
import threading
from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO
from tempfile import TemporaryFile, NamedTemporaryFile
from typing import Iterable, IO

import webdav3
from webdav3.client import Client

from src.data import FullItem
from src.enums import ServiceType
from src.models.post import PostRecord
from src.models.user import UserInfo
from src.models.utils import ServiceKVStore
from src.services.base import PushService
import webdav3.exceptions


@dataclass
class WebDavConfig:
    host: str
    port: int
    use_https: bool
    username: str
    password: str
    path: str
    root_dir: str
    force_direct: bool = False

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
        if conf.force_direct:
            self.client.session.proxies = {}
        self.sem = threading.Semaphore(5)

    def dir_exists(self, path: str):
        try:
            # rclone doesn't allow you check an existing dir
            return self.client.check(path)
        except webdav3.exceptions.MethodNotSupported as e:
            print(e)
            return True

    def ensure_dir(self, tag: str, path: str):
        service_name = f"{SERVICE_NAME}:{tag}"
        if ServiceKVStore.exists(service_name, path):
            return
        if self.dir_exists(path):
            ServiceKVStore.put(service_name, path, {})
            return
        self.client.mkdir(path)
        ServiceKVStore.put(service_name, path, {})

    def write_file(self, tag: str, service: ServiceType, dir_name: str, filename: str, buffer: IO):
        with self.sem:
            self.ensure_dir(tag, service.value)
            self.ensure_dir(tag, f"{service.value}/{dir_name}")
            fp = f"{service.value}/{dir_name}/{filename}"
            with NamedTemporaryFile() as f:
                f.write(buffer.read())
                f.flush()
                try:
                    self.client.upload(fp, f.name)
                except webdav3.exceptions.RemoteParentNotFound as err:
                    print(err)
                    pp = f"{service.value}/{dir_name}"
                    # assert not ServiceKVStore.exists(SERVICE_NAME, pp)
                    # self.client.mkdir(pp)
                    from webdav3.urn import Urn
                    directory_urn = Urn(pp, directory=True)
                    response = self.client.execute_request(action='mkdir', path=directory_urn.quote())
                    assert response in (200, 201), response

                    ServiceKVStore.put(SERVICE_NAME, pp, {})
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
        fp = self.write_file(channel, item.service, dir_name, f"{item.item_id}_info.json", json_buffer)
        PostRecord.put_record(item.service, item.item_id, ServiceType.WebDav, fp, channel)

        for idx, img in enumerate(images):
            fp = self.write_file(channel, item.service, dir_name, f"{item.item_id}_{idx:03d}.png", img)
            PostRecord.put_record(item.service, item.item_id, ServiceType.WebDav, fp, channel)
