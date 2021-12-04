import unittest
import pixivpy3

from src.config import load_config
from src.enums import ServiceType
from src.services.pixiv import PixivServiceBase, PixivLikeSubs

access_token = 'xKbSL3KUiTb2jIKF6eOVmKQzyJzS4vIvLC8g_vbI_uM'
refresh_token = 'nt896L6ptavREBS5qWF5qKjUcxi0wfWBlzqILPjf7rA'

def main():
    api = pixivpy3.PixivAPI()
    api.auth(refresh_token=refresh_token)
    users_works = api.users_works(22612933)
    print(users_works)


if __name__ == '__main__':
    main()
