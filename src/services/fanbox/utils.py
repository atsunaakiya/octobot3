import dataclasses
import unittest
from typing import List, Optional, Tuple

import requests

from src.services.fanbox.page_parser import parse_image_body, parse_article_body
from src.utils.network import get_session_from_cookies_file
from src.utils.project_path import test_dir

@dataclasses.dataclass
class FanboxUser:
    username: str
    user_id: int
    nickname: str

@dataclasses.dataclass
class FanboxPost:
    author: str
    id: int
    title: str
    tags: List[str]
    content: str
    images: List[str]

class FanboxApi:
    def __init__(self, sess: requests.Session):
        self.sess = sess

    def get_on_site(self, artist, url):
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': f'https://{artist}.fanbox.cc/',
            'Origin': f'https://{artist}.fanbox.cc',
            'Connection': 'keep-alive',
            'Sec-GPC': '1',
            'TE': 'trailers',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'same-site',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
        }
        return self.sess.get(url, headers=headers)

    def get_page(self, artist, uid) -> Optional[FanboxPost]:
        url = f'https://api.fanbox.cc/post.info?postId={uid}'
        res = self.get_on_site(artist, url)
        data = res.json()['body']
        page_type = data['type']
        body = data['body']
        if body is None:
            return None
        tags = data['tags']
        title = data['title']
        if page_type == 'article':
            content, images = parse_article_body(body)
        elif page_type == 'image':
            content, images = parse_image_body(body)
        else:
            return None
        return FanboxPost(
            title=title,
            author=artist,
            id=uid,
            tags=tags,
            images=images,
            content=content
        )

    def download_image(self, url):
        res = self.sess.get(url)
        return res.content

    def get_user_info(self, artist):
        url = f'https://api.fanbox.cc/creator.get?creatorId={artist}'
        res = self.get_on_site('www', url)
        data = res.json()
        data = data['body']
        user = data['user']
        return FanboxUser(
            user_id=int(user['userId']),
            nickname=user['name'],
            username=artist
        )

    def list_creator_posts(self, artist, limit):
        url = f'https://api.fanbox.cc/post.listCreator?creatorId={artist}&limit={limit}'
        res = self.get_on_site('www', url)
        data = res.json()
        data = data.get('body')
        if data is None:
            return None
        return [
            int(item['id'])
            for item in data['items']
        ]

    def _parse_items(self, items) -> List[Tuple[str, int]]:
        return [
            (item['creatorId'], int(item['id']))
            for item in items
        ]

    def list_home(self, limit) -> List[Tuple[str, int]]:
        url = f'https://api.fanbox.cc/post.listHome?limit={limit}'
        res = self.get_on_site('www', url)
        data = res.json()
        return self._parse_items(data['body']['items'])

    def list_supporting(self, limit) -> List[Tuple[str, int]]:
        url = f'https://api.fanbox.cc/post.listSupporting?limit={limit}'
        res = self.get_on_site('www', url)
        data = res.json()
        return self._parse_items(data['body']['items'])



class FanboxTestCase(unittest.TestCase):
    def setUp(self) -> None:
        # import logging
        # logging.basicConfig()
        # logging.getLogger().setLevel(logging.DEBUG)
        # requests_log = logging.getLogger("requests.packages.urllib3")
        # requests_log.setLevel(logging.DEBUG)
        # requests_log.propagate = True

        sess = get_session_from_cookies_file('fanbox-bot')
        self.api = FanboxApi(sess)
        test_dir.mkdir(exist_ok=True)

    def test_supporting(self):
        res = self.api.list_supporting(20)
        print(res)

    def test_home(self):
        res = self.api.list_home(20)
        print(res)

    def test_creator(self):
        posts = self.api.list_creator_posts('steelwire', 20)
        print(posts)

    def test_nickname(self):
        res = self.api.get_user_info('steelwire')
        print(res)

    def test_page(self):
        # self.api.get_page('sheep', 3039391)
        # print(self.api.get_page('steelwire', 2941820))
        res = self.api.get_page('steelwire', 2393220)
        image = self.api.download_image(res.images[0])
        print(res)
        with open(test_dir / 'fanbox.png', 'wb') as f:
            f.write(image)
