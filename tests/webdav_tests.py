import unittest
from io import BytesIO

from src.config import load_config
from src.enums import ServiceType
from src.services.webdav import WebDavServiceBase


class MyTestCase(unittest.TestCase):
    def test_something(self):
        config = load_config()
        d = WebDavServiceBase(config.api[ServiceType.WebDav]['default'])
        d.write_file(ServiceType.Twitter, 'Strangestone', 'test.txt', BytesIO("foobar".encode('utf-8')))


if __name__ == '__main__':
    unittest.main()
