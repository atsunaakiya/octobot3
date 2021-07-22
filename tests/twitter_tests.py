import unittest

from src.config import load_config
from src.data import IndexItem
from src.enums import ServiceType
from src.models.connect import connect_db
from src.services.twitter import TwitterUsernameSubs, TwitterService, TweeterServiceBase


class MyTestCase(unittest.TestCase):
    def test_timeline(self):
        connect_db()
        config = load_config()
        conf = config.api[ServiceType.Twitter]['default']
        service = TwitterUsernameSubs(conf)
        print(list(service.subscribe_full('Strangestone')))

    def test_crawler(self):
        connect_db()
        config = load_config()
        conf = config.api[ServiceType.Twitter]['default']
        res = TwitterService(conf).pull_item(IndexItem(item_id='1390984246781644802', service=ServiceType.Twitter))
        print(res)

    def test_like(self):
        config = load_config()
        conf = config.api[ServiceType.Twitter]['default']
        service = TweeterServiceBase(conf)
        print(list(service.get_user_likes('Strangestone')))




if __name__ == '__main__':
    unittest.main()
