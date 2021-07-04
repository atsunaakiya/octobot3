import unittest
from io import BytesIO

from src.config import load_config
from src.enums import ServiceType
from src.models.connect import connect_db
from src.services.webdav import WebDavServiceBase


class MyTestCase(unittest.TestCase):
    def test_something(self):
        config = load_config()
        d = WebDavServiceBase(config.api[ServiceType.WebDav]['default'])
        d.ensure_dir("default", "overflowtest")
        d.write_file(ServiceType.Twitter, 'Strangestone', 'test.txt', BytesIO("foobar".encode('utf-8')))

    def test_info(self):
        config = load_config()
        d = WebDavServiceBase(config.api[ServiceType.WebDav]['new'])
        print(d.dir_exists('twitter'))
        print(d.dir_exists('notexists'))

    def test_create_dir(self):
        config = load_config()
        connect_db()
        d = WebDavServiceBase(config.api[ServiceType.WebDav]['cos'])
        d.ensure_dir('cos', 'twitter/fffff')
        # d.client.mkdir('twitter/fffff')

if __name__ == '__main__':
    unittest.main()
