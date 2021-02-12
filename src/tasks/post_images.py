import traceback
from functools import lru_cache
from io import BytesIO

from src.config import load_config
from src.enums import TaskStatus, TaskStage, ServiceType
from src.models.connect import connect_db
from src.models.item import ItemInfo, SecondaryTask
from src.services import push_services

config = load_config()


def post_images():
    for item in ItemInfo.poll_status(TaskStage.Posting, TaskStatus.Queued):
        channels = ItemInfo.get_channels(item)
        for ch in channels:
            for pipe in config.pipeline[ch].push:
                SecondaryTask.add_task(item.service, item.item_id, pipe.service, pipe.config, ch)
        ItemInfo.set_status(item.service, item.item_id, TaskStage.Posting, TaskStatus.Pending)
    for stype, item_id, ptype, conf, ch in SecondaryTask.poll_tasks():
        SecondaryTask.acquire_task(stype, item_id, ptype, conf, ch)
        print((stype.value, item_id), '=>', (ptype.value, conf))
        item = ItemInfo.get_item(stype, item_id)
        images = [BytesIO(i.read()) for i in ItemInfo.get_images(item)]
        client = get_service(ptype, conf)
        try:
            client.push_item(item, images, ch)
        except Exception as err:
            traceback.print_exc()
            SecondaryTask.release_task(stype, item_id, ptype, conf, ch)
        else:
            SecondaryTask.close_task(stype, item_id, ptype, conf, ch)
        if SecondaryTask.task_done(stype, item_id):
            print("Post Done", (item.service, item.item_id))
            ItemInfo.set_status(item.service, item.item_id, TaskStage.Cleaning, TaskStatus.Queued)



@lru_cache()
def get_service(stype: ServiceType, conf: str):
    service_type = push_services[stype]
    api_conf = config.api[stype][conf]
    return service_type(api_conf)

if __name__ == '__main__':
    connect_db()
    post_images()