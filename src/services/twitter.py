import re
from dataclasses import dataclass
from io import BytesIO
from itertools import chain
from typing import Iterable, IO, List, Tuple, Optional

import requests
from requests import RequestException
from tweepy import TweepError

from src.data import FullItem, IndexItem
from src.enums import ServiceType
from src.errors import FetchFailureError
from src.models.subscribe import MissingSubs
from src.models.user import UserInfo, UserRel
from src.services.base import PullService, SubscribeService
import tweepy


@dataclass
class TwitterConfig:
    consumer_key: str
    consumer_secret: str
    access_key: str
    access_secret: str


@dataclass
class TwitterItem:
    id: int
    text: str
    retweet: bool
    author: Tuple[str, str]
    source: Tuple[str, str]
    images: List[str]


class TweeterServiceBase:
    def __init__(self, config: TwitterConfig):
        auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
        auth.set_access_token(config.access_key, config.access_secret)

        self.api = tweepy.API(auth)

    def get_status(self, sid) -> TwitterItem:
        try:
            status = self.api.get_status(int(sid))
        except TweepError as err:
            raise FetchFailureError(err.reason) from err
        else:
            return status2item(status)

    def get_user_tweets(self, username) -> Iterable[TwitterItem]:
        l: Iterable[tweepy.Status] = self.api.user_timeline(username, count=20)
        for s in l:
            yield status2item(s)

    def get_user_likes(self, username) -> Iterable[TwitterItem]:
        l: Iterable[tweepy.Status] = self.api.favorites(username)
        for s in l:
            yield status2item(s)


class TwitterService(TweeterServiceBase, PullService):
    @classmethod
    def parse_item_id(cls, url) -> Optional[str]:
        res = re.search(r"https?://twitter\.com/\w+/status/(\d+)", url)
        if url is not None:
            return res.group(1)

    def pull_item(self, idx: IndexItem) -> FullItem:
        return item2fullitem(self.get_status(idx.item_id))

    def download_item_image(self, item: FullItem, url: str) -> IO:
        try:
            res = requests.get(url)
        except RequestException as err:
            raise FetchFailureError(str(err)) from err
        else:
            return BytesIO(res.content)


class TwitterUsernameSubs(TweeterServiceBase, SubscribeService):
    @classmethod
    def get_title(cls, name: str) -> Optional[str]:
        return name
        # return UserInfo.get_nickname(ServiceType.Twitter, name)

    @classmethod
    def get_url(cls, name: str) -> Optional[str]:
        return f"https://twitter.com/{name}"

    def subscribe_index(self, name: str) -> Iterable[IndexItem]:
        return []

    def subscribe_full(self, name: str) -> Iterable[FullItem]:
        try:
            tweets = list(self.get_user_tweets(name))
        except TweepError as err:
            MissingSubs.report(ServiceType.Twitter, 'username', name, err.reason)
            print("MISSING SUBS", 'twitter', 'username', name, err.reason)
            return
        for t in tweets:
            UserInfo.set_nickname(ServiceType.Twitter, t.author[1], t.author[0])
            UserInfo.set_nickname(ServiceType.Twitter, t.source[1], t.source[0])
            if t.author[1] == name:
                if t.images:
                    yield item2fullitem(t)
            else:
                UserRel.update_rel(ServiceType.Twitter, t.source[1], t.author[1], str(t.id))

class TwitterLikeSubs(TweeterServiceBase, SubscribeService):
    @classmethod
    def get_title(cls, name: str) -> Optional[str]:
        return name

    @classmethod
    def get_url(cls, name: str) -> Optional[str]:
        return f"https://twitter.com/{name}/likes"

    def subscribe_index(self, name: str) -> Iterable[IndexItem]:
        return []

    def subscribe_full(self, name: str) -> Iterable[FullItem]:
        try:
            tweets = list(self.get_user_likes(name))
        except TweepError as err:
            MissingSubs.report(ServiceType.Twitter, 'username', name, err.reason)
            print("MISSING SUBS", 'twitter', 'username', name, err.reason)
            return
        for t in tweets:
            UserInfo.set_nickname(ServiceType.Twitter, t.author[1], t.author[0])
            if t.images:
                UserRel.update_rel(ServiceType.Twitter, name, t.author[1], str(t.id))
                yield item2fullitem(t)


def status2item(s: tweepy.Status) -> TwitterItem:
    d = s._json
    source_name = d['user']['name']
    source_id = d['user']['screen_name']
    retweet = 'retweeted_status' in d
    if 'retweeted_status' in d:
        p = d['retweeted_status']
        text = p['text']
        item_id = p['id']
        author_name = p['user']['name']
        author_id = p['user']['screen_name']
    else:
        author_name, author_id = source_name, source_id
        item_id = d['id']
        text = d['text']

    def get_images(key):
        if key not in d:
            return []
        if 'media' not in d[key]:
            return []
        urls = [
            m['media_url_https'] or m['media_url']
            for m in d[key]['media']
            if m['type'] == 'photo'
        ]
        urls = [u for u in urls if 'video_thumb' not in u]
        return urls
    images = max(map(get_images, ['extended_entities', 'entities']), key=len)
    return TwitterItem(
        retweet=retweet,
        author=(author_name, author_id),
        source=(source_name, source_id),
        images=list(images),
        id=item_id,
        text=text
    )


def item2fullitem(t: TwitterItem) -> FullItem:
    name, uid = t.author
    url = f"https://twitter.com/{uid}/status/{t.id}"
    return FullItem(content=t.text, item_id=str(t.id), service=ServiceType.Twitter,
                    source_id=uid, image_urls=t.images, url=url)
