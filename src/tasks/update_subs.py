from functools import lru_cache

from src.config import load_config
from src.enums import ServiceType, TaskStage, TaskStatus
from src.models.connect import connect_db
from src.models.item import ItemInfo
from src.models.subscribe import SubscribeSource
from src.services import subscribe_services


def update_subs():
    config = load_config()
    for (stype, sfunc), service_type in subscribe_services.items():
        service_conf = list(config.api[stype].values())[0]
        service = service_type(service_conf)
        for name, channels in SubscribeSource.get_subs(stype, sfunc):
            for item in service.subscribe_index(name):
                ItemInfo.add_index(item, channels)
                print(stype.value, sfunc, name, item)
                if not ItemInfo.exists(item.service, item.item_id):
                    ItemInfo.set_status(item.service, item.item_id, TaskStage.Fetching, TaskStatus.Queued)
            for item in service.subscribe_full(name):
                ItemInfo.add_item(item, channels)
                print(stype.value, sfunc, name, item)
                if not ItemInfo.exists(item.service, item.item_id):
                    ItemInfo.set_status(item.service, item.item_id, TaskStage.Downloading, TaskStatus.Queued)



if __name__ == '__main__':
    connect_db()
    update_subs()
