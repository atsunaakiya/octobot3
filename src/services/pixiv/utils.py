import dataclasses
import json
import shutil
import unittest
import urllib.parse
from io import BytesIO
from typing import List, Optional

import requests
from pyquery import PyQuery as pq


from src.utils.network import get_session_from_cookies_file
from src.utils.project_path import test_dir


@dataclasses.dataclass
class PixivUser:
    name: str
    id: int

@dataclasses.dataclass
class PixivIllustrate:
    title: str
    description: str
    tags: List[str]
    images: List[str]
    author_username: str

class PixivAPI:
    def __init__(self, sess: requests.Session):
        self.sess = sess
        sess.headers['Referer'] = 'https://www.pixiv.net/'

    def get_meta_data(self, url):
        res = self.sess.get(url)
        doc = pq(res.text)
        data = doc('#meta-preload-data').attr('content')
        data = json.loads(data)
        return data

    def get_user(self, uid: int):
        data = self.get_meta_data(f'https://www.pixiv.net/users/{uid}')
        return PixivUser(
            name=data['user'][str(uid)]['name'],
            id=int(data['user'][str(uid)]['userId'])
        )

    def get_illustrate(self, uid: int):
        data = self.get_meta_data(f'https://www.pixiv.net/artworks/{uid}')
        data = data['illust'][str(uid)]
        title = data['title']
        desc = data['description']
        tags = [
            t['tag']
            for t in data['tags']['tags']
        ]
        pages = self.sess.get(f'https://www.pixiv.net/ajax/illust/{uid}/pages').json()
        urls = [
            p['urls']['original']
            for p in pages['body']
        ]
        username = data['userName']
        return PixivIllustrate(
            title=title,
            description=desc,
            tags=tags,
            images=urls,
            author_username=username
        )

    def download_image(self, url):
        headers = {
            'Sec-Fetch-Dest': 'image',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'cross-site',
        }
        res = self.sess.get(url, headers=headers)
        return BytesIO(res.content)

    def get_bookmarks(self, user_id: int, page: int, hidden=False) -> List[int]:
        page_size = 48
        url = f'https://www.pixiv.net/ajax/user/{user_id}/illusts/bookmarks?tag=&offset={page * page_size}&limit={page_size}&lang=zh'
        if hidden:
            url += '&rest=hide'
        else:
            url += '&rest=show'
        res = self.sess.get(url)
        data = res.json()
        return [
            int(w['id'])
            for w in data['body']['works']
        ]

    def search(self, tags: List[str], page: int):
        encoded_tags = urllib.parse.quote(' '.join(tags))
        url = f'https://www.pixiv.net/ajax/search/artworks/{encoded_tags}?p={page+1}'
        res = self.sess.get(url)
        data = res.json()
        return [
            int(w['id'])
            for w in data['body']['illustManga']['data']
        ]


class PixivAPITest(unittest.TestCase):
    def setUp(self) -> None:
        sess = get_session_from_cookies_file('bot')
        self.api = PixivAPI(sess)
        test_dir.mkdir(exist_ok=True)

    def test_user(self):
        data = self.api.get_user(75913411)
        print(data)

    def test_illustrate(self):
        data = self.api.get_illustrate(87622911)
        image_data = self.api.download_image(data.images[0])
        with (test_dir / 'illustrate_test.jpg').open('wb') as f:
            shutil.copyfileobj(image_data, f)

    def test_bookmarks(self):
        data = self.api.get_bookmarks(75913411, 0)
        print(data)
        data = self.api.get_bookmarks(75913411, 0, True)
        print(data)

    def test_search(self):
        data = self.api.search(['魈', '重雲'], 0)
        print(data)

