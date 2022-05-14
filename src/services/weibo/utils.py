import dataclasses
import re
import unittest
from typing import List, Optional

import requests

from src.utils.network import get_session_from_cookies_file
from src.utils.project_path import test_dir


@dataclasses.dataclass
class WeiboItem:
    weibo_id: str
    user_id: int
    user_nickname: str
    content: str
    images: List[str]


class WeiboAPI:
    sess: requests.Session

    def __init__(self, sess: requests.Session):
        self.sess = sess
        self._user_id = None

    def get_like_list(self, user_id: int, page: int) -> List[WeiboItem]:
        url = f"https://weibo.com/ajax/statuses/likelist?uid={user_id}&page={page+1}"
        res = self.sess.get(url)
        data = res.json()
        items_raw = data['data']['list']
        items = [self._parse_item(it) for it in items_raw if it.get('deleted') != '1']
        return items

    def get_weibo(self, weibo_id) -> Optional[WeiboItem]:
        url = f'https://weibo.com/ajax/statuses/show?id={weibo_id}'
        res = self.sess.get(url)
        if res.status_code == 400:
            return None
        assert res.status_code == 200
        data = res.json()
        return self._parse_item(data)

    def _parse_item(self, data) -> WeiboItem:
        weibo_id = data['mblogid']
        content = data['text_raw']
        user_nickname = data['user']['screen_name']
        user_id = data['user']['id']
        pic_info = data.get('pic_infos')
        if pic_info is None:
            image_urls = []
        else:
            image_urls = [pic_info[pic_id]['original']['url'] for pic_id in data['pic_ids']]
        return WeiboItem(
            weibo_id=weibo_id,
            content=content,
            user_nickname=user_nickname,
            user_id=user_id,
            images=image_urls
        )

    def get_user_id(self) -> int:
        if self._user_id is None:
            url = f'https://weibo.com'
            res = self.sess.get(url)
            body = res.text
            user_id = re.search(r'"user":{"id":(\d+),', body).group(1)
            self._user_id = int(user_id)
        return self._user_id


class WeiboCase(unittest.TestCase):
    def setUp(self) -> None:
        sess = get_session_from_cookies_file('weibo')
        self.api = WeiboAPI(sess)
        test_dir.mkdir(exist_ok=True)

    def test_get_id(self):
        user_id = self.api.get_user_id()
        print('User Id:', user_id)

    def test_like(self):
        user_id = self.api.get_user_id()
        items = self.api.get_like_list(user_id, 1)
        print(items)

    def test_item(self):
        item = self.api.get_weibo('LsOycmhQi')
        self.assertIsNotNone(item)
        print(item)

    def test_deleted_item(self):
        item = self.api.get_weibo('LrLPBmiTA')
        self.assertIsNone(item)




if __name__ == '__main__':
    unittest.main()
