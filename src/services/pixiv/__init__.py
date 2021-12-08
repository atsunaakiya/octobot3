import re

from dataclasses import dataclass
from typing import Optional, Iterable, IO


from src.data import FullItem, IndexItem
from src.enums import ServiceType
from src.models.user import UserInfo
from src.services import SubscribeService, PullService
from src.utils.network import get_session_from_cookies_file


@dataclass
class PixivConfig:
    cookies: str



class PixivServiceBase:
    config: PixivConfig
    def __init__(self, config: PixivConfig):
        self.config = config
        self.sess = get_session_from_cookies_file(config.cookies)

class PixivService(PixivServiceBase, PullService):
    def pull_item(self, index_item: IndexItem) -> FullItem:
        pass

    def download_item_image(self, item: FullItem, url: str) -> IO:
        pass

    @classmethod
    def parse_item_id(cls, url) -> Optional[str]:
        res = re.search(r'pixiv\.net/users/(\d+)', url)
        return res and res.group(1)


class PixivLikeSubs(PixivServiceBase, SubscribeService):
    def subscribe_index(self, name: str) -> Iterable[IndexItem]:
        pass

    def subscribe_full(self, name: str) -> Iterable[FullItem]:
        return []

    @classmethod
    def get_title(cls, name: str) -> Optional[str]:
        return UserInfo.get_nickname(ServiceType.Pixiv, name)

    @classmethod
    def get_url(cls, name: str) -> Optional[str]:
        return f'https://www.pixiv.net/users/{name}'

