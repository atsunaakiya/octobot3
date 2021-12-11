import time
import traceback
from functools import lru_cache

from src.config import load_config, RootConfig
from src.data import IndexItem
from src.enums import TaskStage, TaskStatus, ServiceType
from src.errors import FetchFailureError
from src.models.connect import connect_db
from src.models.item import ItemInfo
from src.services import pull_services

config = load_config()


def update_index():
    for item in ItemInfo.poll_status_index(TaskStage.Fetching, TaskStatus.Queued, limit=config.limit.fetch):
        service = get_service(item.service)
        ItemInfo.set_status(item.service, item.item_id, TaskStage.Fetching, TaskStatus.Pending)
        try:
            full_item = service.pull_item(IndexItem(item.service, item.item_id))
        except Exception as err:
            traceback.print_exc()
            ItemInfo.set_status(item.service, item.item_id, TaskStage.Fetching, TaskStatus.Queued)
        else:
            print(full_item)
            if full_item is None:
                ItemInfo.set_status(item.service, item.item_id, TaskStage.Fetching, TaskStatus.Failed)
            else:
                ItemInfo.add_item(full_item, [])
                ItemInfo.set_status(item.service, item.item_id, TaskStage.Downloading, TaskStatus.Queued)
        time.sleep(1)
    ItemInfo.abandon_tasks(TaskStage.Fetching, TaskStatus.Queued, 20, TaskStage.Fetching, TaskStatus.Failed)


@lru_cache()
def get_service(stype: ServiceType):
    service_type = pull_services[stype]
    api_conf = list(config.api[stype].values())[0]
    return service_type(api_conf)




if __name__ == '__main__':
    connect_db()
    update_index()
