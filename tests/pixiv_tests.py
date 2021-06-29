import unittest

from src.config import load_config
from src.enums import ServiceType
from src.services.pixiv import PixivServiceBase, PixivLikeSubs


class MyTestCase(unittest.TestCase):
    def test_get_token(self):
        pass

    def test_url(self):
        config = load_config()
        api = config.api[ServiceType.Pixiv]['zb']


if __name__ == '__main__':
    unittest.main()
