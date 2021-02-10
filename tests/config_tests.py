import json
import unittest

from src.config import load_config
from src.data import FullItem
from src.enums import ServiceType
from src.models import connect_db


class MyTestCase(unittest.TestCase):
    def test_config(self):
        print(load_config())

    def test_db(self):
        connect_db()

    def test_jsonify(self):
        print(json.dumps(FullItem(
            service=ServiceType.Twitter,
            item_id='233',
            source_id='666',
            content='content',
            image_urls=['image.png'],
            url='url'
        ).to_dict()))


if __name__ == '__main__':
    unittest.main()
