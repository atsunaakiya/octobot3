from dataclasses import dataclass
from typing import List, Iterable, IO

import telegram
from telegram import InputMediaPhoto

from src.data import FullItem
from src.enums import ServiceType
from src.models.post import PostRecord
from src.services.base import PushService


@dataclass
class TelegramConfig:
    channels: List[str]
    token: str
    media_group_limit: int


class TelegramServiceBase:
    def __init__(self, config: TelegramConfig):
        self.bot = telegram.Bot(token=config.token)
        self.channels = config.channels

    def post_images(self, images: List[IO]):

        media = [
            InputMediaPhoto(i)
            for i in images
        ]
        message_id = []
        for ch in self.channels:
            chat = self.bot.get_chat(ch)
            messages = chat.send_media_group(media)
            message_id.extend([str(m.message_id) for m in messages])
        return message_id


class TelegramService(PushService, TelegramServiceBase):
    def push_item(self, item: FullItem, images: List[IO], channel: str):
        for i in range(0, len(images), 10):
            id_list = self.post_images(images[i:i+10])
            for mid in id_list:
                PostRecord.put_record(item.service, item.item_id, ServiceType.Telegram, mid, channel)

