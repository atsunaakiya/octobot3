from enum import Enum


class ServiceType(Enum):
    Twitter = 'twitter'
    Telegram = 'telegram'
    WebDav = 'webdav'
    Mega = 'mega'
    Pixiv = 'pixiv'
    Fanbox = 'fanbox'
    Local = 'local'


class TaskStage(Enum):
    Fetching = 'fetching'
    Downloading = 'downloading'
    Posting = 'posting'
    Cleaning = 'cleaning'
    Done = 'done'


class TaskStatus(Enum):
    Queued = 'queued'
    Failed = 'failed'
    Pending = 'pending'


class SecondaryTaskStatus(Enum):
    Queued = 'queued'
    Pending = 'pending'
    Finished = 'finished'


class SubscribeStatus(Enum):
    enabled = 'enabled'
    deleted = 'deleted'
    missing = 'missing'
