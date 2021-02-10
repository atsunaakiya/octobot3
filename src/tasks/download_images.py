import time
from io import BytesIO

from PIL import Image
from functools import lru_cache

from src.config import load_config
from src.enums import ServiceType, TaskStage, TaskStatus
from src.errors import FetchFailureError
from src.models.connect import connect_db
from src.models.item import ItemInfo
from src.services import pull_services

config = load_config()

def download_images():
    for item in ItemInfo.poll_status(TaskStage.Downloading, TaskStatus.Queued, limit=config.limit.download):
        service = get_service(item.service)
        try:
            for url in item.image_urls:
                print(url)
                raw = service.download_item_image(item, url)
                img = Image.open(raw)
                with BytesIO() as buf:
                    img.save(buf, format="PNG")
                    buf.seek(0)
                    ItemInfo.save_image(item, url, buf)
                time.sleep(1)
        except FetchFailureError as err:
            print(err)
            ItemInfo.set_status(item.service, item.item_id, TaskStage.Downloading, TaskStatus.Failed)
        else:
            ItemInfo.set_status(item.service, item.item_id, TaskStage.Posting, TaskStatus.Queued)

@lru_cache()
def get_service(stype: ServiceType):
    service_type = pull_services[stype]
    api_conf = list(config.api[stype].values())[0]
    return service_type(api_conf)

if __name__ == '__main__':
    connect_db()
    download_images()
