import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Mapping, Generic, TypeVar, List, Tuple

from pip._vendor import toml

from src.enums import ServiceType
from src.services import APIConfig, parse_api
from src.services.base import BaseService

T = TypeVar('T')


@dataclass
class PipelineItem(Generic[T]):
    service: T
    config: str


@dataclass
class PipelineConfig:
    subscribe: List[PipelineItem[Tuple[ServiceType, str]]]
    pull: List[PipelineItem[ServiceType]]
    push: List[PipelineItem[ServiceType]]


@dataclass
class MongoConfig:
    host: str
    port: int
    db: str


@dataclass
class ServerConfig:
    host: str
    port: int
    debug: bool


@dataclass
class LimitConfig:
    fetch: int
    download: int

@dataclass
class RootConfig:
    server: ServerConfig
    db: MongoConfig
    api: APIConfig
    pipeline: Mapping[str, PipelineConfig]
    limit: LimitConfig



def parse_pipeline_config(d) -> PipelineConfig:
    subscribe = []
    pull = []
    push = []
    for s in d['subscribe']:
        t, n, c = re.search(r"^(\w+)\.(\w+):(\w+)$", s).groups()
        subscribe.append(PipelineItem(service=(ServiceType(t), n), config=c))
    for s in d['pull']:
        t, c = s.split(":")
        pull.append(PipelineItem(service=ServiceType(t), config=c))
    for s in d['push']:
        t, c = s.split(":")
        push.append(PipelineItem(service=ServiceType(t), config=c))
    return PipelineConfig(
        subscribe=subscribe,
        pull=pull,
        push=push
    )


def parse_config(d) -> RootConfig:
    server = ServerConfig(**d['server'])
    db = MongoConfig(**d['db'])
    api = parse_api(d['api'])
    pipeline = {
        nm: parse_pipeline_config(e)
        for nm, e in d['pipeline'].items()
    }
    limit = LimitConfig(**d['limit'])
    return RootConfig(
        server=server,
        db=db,
        api=api,
        pipeline=pipeline,
        limit=limit
    )


default_config_file = Path(__file__).parent.parent / 'config.toml'


@lru_cache(1)
def load_config() -> RootConfig:
    with open(default_config_file) as f:
        return parse_config(toml.load(f))
