import re
import time
from dataclasses import dataclass
from io import BytesIO
from typing import Optional, IO, Iterable, List

from src.data import IndexItem, FullItem
from src.enums import ServiceType
from src.models.user import UserInfo
from src.services import PullService, SubscribeService
from src.services.fanbox.utils import FanboxApi
from src.utils.network import get_session_from_cookies_file


@dataclass
class FanboxConfig:
    cookies: str


class FanboxServiceBase:
    config: FanboxConfig
    def __init__(self, config: FanboxConfig):
        self.config = config
        self.sess = get_session_from_cookies_file(config.cookies)
        self.api = FanboxApi(self.sess)

    def get_nickname(self, name: str):
        nickname = UserInfo.get_nickname(ServiceType.Fanbox, name)
        if nickname is None:
            user = self.api.get_user_info(name)
            nickname = user.nickname
            UserInfo.set_nickname(ServiceType.Fanbox, name, nickname)
        return nickname

    @staticmethod
    def split_item_id(item_id):
        artist, article_id = item_id.split('@')
        article_id = int(article_id)
        return artist, article_id

    @staticmethod
    def to_item_id(artist, post_id):
        return f'{artist}@{post_id}'


class FanboxService(FanboxServiceBase, PullService):
    def pull_item(self, index_item: IndexItem) -> Optional[FullItem]:
        artist, article_id = self.split_item_id(index_item.item_id)
        data = self.api.get_page(artist, article_id)
        if data is None:
            return None
        content = f"{' '.join(f'#{t}' for t in data.tags)}\n\n{data.content}"
        self.get_nickname(artist)
        return FullItem(
            service=ServiceType.Fanbox,
            item_id=index_item.item_id,
            source_id=artist,
            content=content,
            image_urls=data.images,
            url=f"https://www.fanbox.cc/@{artist}/posts/{article_id}",
            tags=data.tags
        )

    def download_item_image(self, item: FullItem, url: str) -> IO:
        time.sleep(5)
        return BytesIO(self.api.download_image(url))

    @classmethod
    def parse_item_id(cls, url) -> Optional[str]:
        res = re.search(r'www\.fanbox\.cc/@(\w+)/posts/(\d+)', url)
        if res is None:
            res = re.search(r'(\w+)\.fanbox\.cc/posts/(\d+)', url)
        if res is None:
            return None
        artist, post_id = res.groups()
        return cls.to_item_id(artist, post_id)

    @classmethod
    def convert_username(cls, name: str):
        nickname = UserInfo.get_nickname(ServiceType.Fanbox, str(name)) or ''
        return f'{nickname}({name})'


class FanboxUsernameSubs(FanboxServiceBase, SubscribeService):
    def subscribe_index(self, name: str) -> Iterable[IndexItem]:
        for post_id in self.api.list_creator_posts(name, 30):
            uid = self.to_item_id(name, post_id)
            yield IndexItem(ServiceType.Fanbox, uid)

    def subscribe_full(self, name: str) -> Iterable[FullItem]:
        return []

    @classmethod
    def get_title(cls, name: str) -> Optional[str]:
        return FanboxService.convert_username(name)

    @classmethod
    def get_url(cls, name: str) -> Optional[str]:
        return f'https://{name}.fanbox.cc/'


class FanboxReflect(FanboxServiceBase, SubscribeService):
    def subscribe_index(self, name: str) -> Iterable[IndexItem]:
        if name == 'home':
            home = self.api.list_home(30)
            return [
                IndexItem(
                    service=ServiceType.Fanbox,
                    item_id=self.to_item_id(artist, post_id)
                )
                for artist, post_id in home
            ]
        elif name == 'supporting':
            home = self.api.list_supporting(30)
            return [
                IndexItem(
                    service=ServiceType.Fanbox,
                    item_id=self.to_item_id(artist, post_id)
                )
                for artist, post_id in home
            ]
        else:
            raise ValueError(name)

    def subscribe_full(self, name: str) -> Iterable[FullItem]:
        return []

    @classmethod
    def get_title(cls, name: str) -> Optional[str]:
        return name

    @classmethod
    def get_url(cls, name: str) -> Optional[str]:
        return f'https://www.fanbox.cc/'

    @classmethod
    def options(cls) -> Optional[List[str]]:
        return ['home', 'supporting']
