from dataclasses import dataclass
from typing import Callable, Any, Mapping, Tuple, Type, Dict

from src.enums import ServiceType
from src.services.base import PullService, PushService, SubscribeService
from src.services.telegram import TelegramService, TelegramConfig
from src.services.twitter import TwitterService, TwitterUsernameSubs, TwitterConfig
from src.services.webdav import WebDavService, WebDavConfig

config_index: Mapping[ServiceType, Callable[[Dict], Any]] = {
    ServiceType.Twitter: TwitterConfig,
    ServiceType.Telegram: TelegramConfig,
    ServiceType.WebDav: WebDavConfig,
}

subscribe_services: Mapping[Tuple[ServiceType, str], Type[SubscribeService]] = {
    (ServiceType.Twitter, 'username'): TwitterUsernameSubs
}

pull_services: Mapping[ServiceType, Type[PullService]] = {
    ServiceType.Twitter: TwitterService
}

push_services: Mapping[ServiceType, Type[PushService]] = {
    ServiceType.WebDav: WebDavService,
    ServiceType.Telegram: TelegramService,
}


APIConfig = Mapping[ServiceType, Mapping[str, Any]]


def parse_api(d) -> APIConfig:
    return {
        t: {
            n: config_index[t](**v)
            for n, v in d[t.value].items()
        }
        for t in ServiceType
    }