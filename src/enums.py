from enum import Enum


class ServiceType(Enum):
    Twitter = 'twitter'
    Telegram = 'telegram'
    WebDav = 'webdav'


class TaskStage(Enum):
    Fetching = 'fetching'
    Downloading = 'downloading'
    Posting = 'posting'
    Cleaning = 'cleaning'
    Done = 'done'


class TaskStatus(Enum):
    Queued = 'queued'
    Failed = 'failed'
