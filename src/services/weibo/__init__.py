import dataclasses
import re
from io import BytesIO
from typing import Optional, IO, Iterable, List

from requests import RequestException

from src.data import FullItem, IndexItem
from src.enums import ServiceType
from src.errors import FetchFailureError
from src.models.user import UserInfo
from src.services import PullService, SubscribeService
from src.services.weibo.utils import WeiboAPI, WeiboItem
from src.utils.network import get_session_from_cookies_file


@dataclasses.dataclass
class WeiboConfig:
    cookies: str


class WeiboServiceBase:
    def __init__(self, config: WeiboConfig):
        self.config = config
        self.sess = get_session_from_cookies_file(config.cookies)
        self.api = WeiboAPI(self.sess)

    @staticmethod
    def weibo_to_full_item(item: WeiboItem):
        return FullItem(
            service=ServiceType.Weibo,
            item_id=item.weibo_id,
            content=item.content,
            image_urls=item.images,
            source_id=str(item.user_id),
            url=f'https://weibo.com/{item.user_id}/{item.weibo_id}'
        )


class WeiboService(WeiboServiceBase, PullService):
    def pull_item(self, index_item: IndexItem) -> FullItem:
        item = self.api.get_weibo(index_item.item_id)
        if item is None:
            return None
        UserInfo.set_nickname(ServiceType.Weibo, str(item.user_id), item.user_nickname)
        return self.weibo_to_full_item(item)

    def download_item_image(self, item: FullItem, url: str) -> IO:
        try:
            res = self.sess.get(url)
        except RequestException as err:
            raise FetchFailureError(str(err)) from err
        else:
            return BytesIO(res.content)

    @classmethod
    def parse_item_id(cls, url) -> Optional[str]:
        res = re.search(r'https?://weibo\.com/\d+/(\w+)', url)
        if res is not None:
            return res.group(1)


class WeiboReflect(WeiboServiceBase, SubscribeService):
    def subscribe_index(self, name: str) -> Iterable[IndexItem]:
        return []

    def subscribe_full(self, name: str) -> Iterable[FullItem]:
        if name == 'like':
            user_id = self.api.get_user_id()
            results = self.api.get_like_list(user_id, 0)
            return [
                self.weibo_to_full_item(it)
                for it in results
                if it.images
            ]
        else:
            raise ValueError(name)

    @classmethod
    def get_title(cls, name: str) -> Optional[str]:
        pass

    @classmethod
    def get_url(cls, name: str) -> Optional[str]:
        return 'https://weibo.com'

    @classmethod
    def options(cls) -> Optional[List[str]]:
        return ['like']
