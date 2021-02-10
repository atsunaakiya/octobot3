from functools import lru_cache
from io import BytesIO

from src.config import load_config
from src.enums import TaskStatus, TaskStage, ServiceType
from src.models.connect import connect_db
from src.models.item import ItemInfo
from src.services import push_services

config = load_config()


def post_images():
    for item in ItemInfo.poll_status(TaskStage.Posting, TaskStatus.Queued):
        channels = ItemInfo.get_channels(item)
        for ch in channels:
            for pipe in config.pipeline[ch].push:
                print((item.service.value, item.item_id), '=>', (pipe.service.value, pipe.config))
                service = get_service(pipe.service, pipe.config)
                images = [i.read() for i in ItemInfo.get_images(item)]
                service.push_item(item, list(map(BytesIO, images)), ch)
        ItemInfo.set_status(item.service, item.item_id, TaskStage.Cleaning, TaskStatus.Queued)


@lru_cache()
def get_service(stype: ServiceType, conf: str):
    service_type = push_services[stype]
    api_conf = config.api[stype][conf]
    return service_type(api_conf)

if __name__ == '__main__':
    connect_db()
    post_images()