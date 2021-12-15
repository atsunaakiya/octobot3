import dataclasses
import json
import shutil
import unittest
import urllib.parse
from io import BytesIO
from json import JSONDecodeError
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
    id: int
    title: str
    description: str
    tags: List[str]
    images: List[str]
    author_id: int


class PixivAPI:
    def __init__(self, sess: requests.Session):
        self.sess = sess
        sess.headers['Referer'] = 'https://www.pixiv.net/'

    def get_meta_data(self, url):
        res = self.sess.get(url)
        doc = pq(res.text)
        data = doc('#meta-preload-data').attr('content')
        if data is None:
            if doc('.error-message'):
                return None
            else:
                raise ValueError('Pixiv Page Changed')
        try:
            data = json.loads(data)
        except TypeError as err:
            print(f'data={repr(data)}')
            # print(res.text)
            raise err
        except JSONDecodeError as err:
            print(data)
            raise err
        return data

    def get_user(self, uid: int):
        data = self.get_meta_data(f'https://www.pixiv.net/users/{uid}')
        return PixivUser(
            name=data['user'][str(uid)]['name'],
            id=int(data['user'][str(uid)]['userId'])
        )

    def get_illustrate(self, uid: int):
        data = self.get_meta_data(f'https://www.pixiv.net/artworks/{uid}')
        if data is None:
            return None
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
        user_id = int(data['userId'])
        return PixivIllustrate(
            id=uid,
            title=title,
            description=desc,
            tags=tags,
            images=urls,
            author_id=user_id
        )

    def user_illustrates(self, uid: int):
        url = f'https://www.pixiv.net/ajax/user/{uid}/profile/all?lang=zh'
        data = self.sess.get(url).json()
        data = data['body']
        id_list = list(data['illusts'].keys()) + list(data['manga'].keys())
        return id_list

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

    def following_illust(self, page):
        url = f"https://www.pixiv.net/ajax/follow_latest/illust?p={page+1}&mode=all&lang=zh"
        res = self.sess.get(url)
        data = res.json()
        return data['body']['page']['ids']


class PixivAPITest(unittest.TestCase):
    def setUp(self) -> None:
        sess = get_session_from_cookies_file('bot')
        self.api = PixivAPI(sess)
        test_dir.mkdir(exist_ok=True)

    def test_following_illust(self):
        data = self.api.following_illust(0)
        print(data)

    def test_user(self):
        data = self.api.get_user(75913411)
        print(data)

    def test_not_exist(self):
        res = self.api.get_illustrate(233333)
        print(res)
        self.assertIsNone(res)

    def test_illustrate(self):
        data = self.api.get_illustrate(87622911)
        print(data)
        image_data = self.api.download_image(data.images[0])
        with (test_dir / 'illustrate_test.jpg').open('wb') as f:
            shutil.copyfileobj(image_data, f)

    def test_user_illustrates(self):
        data = self.api.user_illustrates(6210796)
        print(data)

    def test_just_image(self):
        image_data = self.api.download_image('https://i.pximg.net/img-original/img/2021/02/11/17/35/32/87687896_p0.png')
        with (test_dir / 'illustrate_test2.jpg').open('wb') as f:
            shutil.copyfileobj(image_data, f)

    def test_bookmarks(self):
        data = self.api.get_bookmarks(75913411, 0)
        print(data)
        data = self.api.get_bookmarks(75913411, 0, True)
        print(data)

    def test_search(self):
        data = self.api.search(['魈', '重雲'], 0)
        print(data)

