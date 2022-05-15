import json
import unittest
from typing import Dict

import requests

from src.utils.project_path import project_root

cookies_root = project_root / 'cookies'
cookie_jar_root = project_root / 'cookie-jar'


def get_session_from_cookies(cookies: Dict[str, str]):
    sess = requests.session()
    for k, v in cookies.items():
        sess.cookies.set(k, v)
    sess.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0'
    return sess


def get_session_from_cookies_file(name):
    """
    Export a cookies json file with https://github.com/Moustachauve/cookie-editor
    """
    cookies_fp = cookies_root / f'{name}.json'
    with cookies_fp.open() as f:
        cookies = json.load(f)
        cookies = {
            c['name']: c['value']
            for c in cookies
        }
    return get_session_from_cookies(cookies)


class TestNetworkCases(unittest.TestCase):
    def test_cookies_root(self):
        cookies = {'test': 'foo'}
        sess = get_session_from_cookies(cookies)
        res = sess.get('https://httpbin.org/cookies')
        data = res.json()
        self.assertEqual(cookies, data['cookies'])

