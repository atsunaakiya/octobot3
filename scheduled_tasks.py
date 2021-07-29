import time
import traceback
from functools import partial

from src.models.connect import connect_db
from src.models.item import ItemInfo
from src.tasks.clean_cache import clean_cache
from src.tasks.update_index import update_index
from src.tasks.download_images import download_images
from src.tasks.post_images import post_images
from src.tasks.update_subs import update_subs

task_conf = {
    'update_subs': (57, update_subs),
    'update_index': (13, update_index),
    'download_images': (8, download_images),
    'post_images': (5, post_images),
    'clean_cache': (60, clean_cache)
}

def try_to_run(func):
    try:
        func()
    except KeyboardInterrupt as err:
        raise err
    except:
        traceback.print_exc()


def run_schedule(task):
    minutes, func = task_conf[task]
    func = partial(try_to_run, func)
    connect_db()
    ItemInfo.clean_pending_items()
    while True:
        try:
            func()
        except KeyboardInterrupt:
            break
        time.sleep(minutes * 60)


