import time
from dataclasses import dataclass
from io import BytesIO
from typing import List, Iterable, IO

import telegram
from telegram import InputMediaPhoto

from src.data import FullItem
from src.enums import ServiceType
from src.models.post import PostRecord
from src.services.base import PushService
from PIL import Image


@dataclass
class TelegramConfig:
    channels: List[str]
    token: str
    media_group_limit: int
    attach_source: bool = False


class TelegramServiceBase:
    def __init__(self, config: TelegramConfig):
        self.bot = telegram.Bot(token=config.token)
        self.channels = config.channels
        self.config = config

    @staticmethod
    def resize_image(image_io):
        edge_limit = 1000
        img = Image.open(image_io)
        width, height = img.size
        max_edge = max(width, height)
        if max_edge > edge_limit:
            scale = edge_limit / max_edge
            width = int(width * scale)
            height = int(height * scale)
            img = img.resize((width, height))
        img = img.convert('RGB')
        buf = BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)
        time.sleep(2)
        return buf

    def post_images(self, images: List[IO], source: str):
        media = [
            InputMediaPhoto(self.resize_image(i))
            for i in images
        ]
        if self.config.attach_source:
            media[0].caption = source
        message_id = []
        for ch in self.channels:
            chat = self.bot.get_chat(ch)
            messages = chat.send_media_group(media)
            message_id.extend([str(m.message_id) for m in messages])
        time.sleep(5)
        return message_id


class TelegramService(PushService, TelegramServiceBase):
    def push_item(self, item: FullItem, images: List[IO], channel: str, converted_username: str):
        for i in range(0, len(images), 10):
            id_list = self.post_images(images[i:i+10], item.url)
            for mid in id_list:
                PostRecord.put_record(item.service, item.item_id, ServiceType.Telegram, mid, channel)

