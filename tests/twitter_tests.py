import unittest

from src.config import load_config
from src.enums import ServiceType
from src.models.connect import connect_db
from src.services.twitter import TwitterUsernameSubs


class MyTestCase(unittest.TestCase):
    def test_timeline(self):
        connect_db()
        config = load_config()
        conf = config.api[ServiceType.Twitter]['default']
        service = TwitterUsernameSubs(conf)
        print(list(service.subscribe_full('Strangestone')))



if __name__ == '__main__':
    unittest.main()
