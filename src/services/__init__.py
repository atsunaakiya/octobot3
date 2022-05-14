from dataclasses import dataclass
from typing import Callable, Any, Mapping, Tuple, Type, Dict

from src.enums import ServiceType
from src.services.base import PullService, PushService, SubscribeService
from src.services.fanbox import FanboxUsernameSubs, FanboxService, FanboxReflect, FanboxConfig
from src.services.local import LocalService, LocalConfig
# from src.services.megasync import MegaService, MegaConfig
from src.services.pixiv import PixivConfig, PixivService, PixivLikeSubs, PixivSearchSubs, PixivIllustSubs
from src.services.telegram_service import TelegramService, TelegramConfig
from src.services.twitter import TwitterService, TwitterUsernameSubs, TwitterConfig, TwitterLikeSubs
from src.services.webdav import WebDavService, WebDavConfig
from src.services.weibo import WeiboReflect, WeiboConfig, WeiboService

config_index: Mapping[ServiceType, Callable[[Dict], Any]] = {
    ServiceType.Twitter: TwitterConfig,
    ServiceType.Telegram: TelegramConfig,
    ServiceType.WebDav: WebDavConfig,
    # ServiceType.Mega: MegaConfig,
    ServiceType.Pixiv: PixivConfig,
    ServiceType.Local: LocalConfig,
    ServiceType.Fanbox: FanboxConfig,
    ServiceType.Weibo: WeiboConfig
}

subscribe_services: Mapping[Tuple[ServiceType, str], Type[SubscribeService]] = {
    (ServiceType.Twitter, 'username'): TwitterUsernameSubs,
    (ServiceType.Twitter, 'likes'): TwitterLikeSubs,
    (ServiceType.Pixiv, 'illust'): PixivIllustSubs,
    (ServiceType.Pixiv, 'likes'): PixivLikeSubs,
    (ServiceType.Pixiv, 'search'): PixivSearchSubs,
    (ServiceType.Fanbox, 'username'): FanboxUsernameSubs,
    (ServiceType.Fanbox, 'reflect'): FanboxReflect,
    (ServiceType.Weibo, 'reflect'): WeiboReflect,
}

pull_services: Mapping[ServiceType, Type[PullService]] = {
    ServiceType.Twitter: TwitterService,
    ServiceType.Pixiv: PixivService,
    ServiceType.Fanbox: FanboxService,
    ServiceType.Weibo: WeiboService
}

push_services: Mapping[ServiceType, Type[PushService]] = {
    ServiceType.WebDav: WebDavService,
    ServiceType.Telegram: TelegramService,
    # ServiceType.Mega: MegaService,
    ServiceType.Local: LocalService
}


APIConfig = Mapping[ServiceType, Mapping[str, Any]]


def parse_api(d) -> APIConfig:
    return {
        t: {
            n: config_index[t](**v)
            for n, v in d[t.value].items()
        }
        for t in ServiceType
        if t.value in d
    }