import re
import urllib.parse

from dataclasses import dataclass
from typing import Optional, Iterable, IO


from src.data import FullItem, IndexItem
from src.enums import ServiceType
from src.models.user import UserInfo
from src.services import SubscribeService, PullService
from src.services.pixiv.utils import PixivAPI
from src.utils.network import get_session_from_cookies_file


@dataclass
class PixivConfig:
    cookies: str


class PixivServiceBase:
    config: PixivConfig
    def __init__(self, config: PixivConfig):
        self.config = config
        self.sess = get_session_from_cookies_file(config.cookies)
        self.api = PixivAPI(self.sess)

    def get_nickname(self, uid: int):
        nickname = UserInfo.get_nickname(ServiceType.Pixiv, str(uid))
        if nickname is None:
            user = self.api.get_user(uid)
            nickname = user.name
            UserInfo.set_nickname(ServiceType.Pixiv, str(uid), nickname)
        return nickname


class PixivService(PixivServiceBase, PullService):
    def pull_item(self, index_item: IndexItem) -> FullItem:
        data = self.api.get_illustrate(int(index_item.item_id))
        content = f"{' '.join(f'#{t}' for t in data.tags)}\n\n{data.description}"
        self.get_nickname(data.author_id)
        return FullItem(
            service=ServiceType.Pixiv,
            item_id=str(data.id),
            source_id=str(data.author_id),
            content=content,
            image_urls=data.images,
            url=f"https://www.pixiv.net/artworks/{index_item.item_id}",
            tags=data.tags
        )

    def download_item_image(self, item: FullItem, url: str) -> IO:
        return self.api.download_image(url)

    @classmethod
    def parse_item_id(cls, url) -> Optional[str]:
        res = re.search(r'pixiv\.net/(\w+/)?artworks/(\d+)', url)
        return res and res.group(2)

    @classmethod
    def convert_username(cls, name: str):
        nickname = UserInfo.get_nickname(ServiceType.Pixiv, str(name)) or ''
        return f'{nickname}({name})'


class PixivIllustSubs(PixivServiceBase, SubscribeService):
    def subscribe_index(self, name: str) -> Iterable[IndexItem]:
        for uid in self.api.user_illustrates(int(name)):
            yield IndexItem(ServiceType.Pixiv, str(uid))

    def subscribe_full(self, name: str) -> Iterable[FullItem]:
        return []

    @classmethod
    def get_title(cls, name: str) -> Optional[str]:
        return PixivService.convert_username(name)

    @classmethod
    def get_url(cls, name: str) -> Optional[str]:
        return f'https://www.pixiv.net/users/{name}/illustrations'


class PixivLikeSubs(PixivServiceBase, SubscribeService):
    def subscribe_index(self, name: str) -> Iterable[IndexItem]:
        for uid in self.api.get_bookmarks(int(name), 0, False):
            yield IndexItem(ServiceType.Pixiv, str(uid))

    def subscribe_full(self, name: str) -> Iterable[FullItem]:
        return []

    @classmethod
    def get_title(cls, name: str) -> Optional[str]:
        return PixivService.convert_username(name)

    @classmethod
    def get_url(cls, name: str) -> Optional[str]:
        return f'https://www.pixiv.net/users/{name}/bookmarks/artworks'


class PixivSearchSubs(PixivServiceBase, SubscribeService):
    def subscribe_index(self, name: str) -> Iterable[IndexItem]:
        for uid in self.api.search(name.split(' '), 0):
            yield IndexItem(ServiceType.Pixiv, str(uid))

    def subscribe_full(self, name: str) -> Iterable[FullItem]:
        return []

    @classmethod
    def get_title(cls, name: str) -> Optional[str]:
        return name

    @classmethod
    def get_url(cls, name: str) -> Optional[str]:
        name = urllib.parse.quote(name)
        return f'https://www.pixiv.net/tags/{name}/artworks'

