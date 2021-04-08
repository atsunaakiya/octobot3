import unittest
from io import BytesIO
from pathlib import Path

import mega

from src.config import load_config
from src.enums import ServiceType
from src.services import MegaConfig, MegaService


class MyTestCase(unittest.TestCase):
    def test_create_folder(self):
        config = load_config()
        conf: MegaConfig = config.api[ServiceType.Mega]['default']
        client = mega.Mega()
        client.login(conf.username, conf.password)
        client.create_folder(conf.root)

    def test_write(self):
        config = load_config()
        conf: MegaConfig = config.api[ServiceType.Mega]['default']
        client = MegaService(conf)
        print(client.client.find(conf.root, exclude_deleted=True))
        print(client.ensure_dir(Path("/FU/CK2")))
        # client.write_file(client.root / "test2.txt", BytesIO(b"Test"))


if __name__ == '__main__':
    unittest.main()
