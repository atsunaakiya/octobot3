from src.config import load_config
from src.enums import TaskStatus, TaskStage
from src.models.connect import connect_db
from src.models.item import ItemInfo

config = load_config()

def clean_cache():
    for item in ItemInfo.poll_status(TaskStage.Cleaning, TaskStatus.Queued):
        ItemInfo.clean_cache(item)
        ItemInfo.set_status(item.service, item.item_id, TaskStage.Done, TaskStatus.Queued)

if __name__ == '__main__':
    connect_db()
    clean_cache()
