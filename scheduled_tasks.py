import time
from threading import Thread, Event

import schedule

from src.models.connect import connect_db
from src.models.item import ItemInfo
from src.tasks.clean_cache import clean_cache
from src.tasks.update_index import update_index
from src.tasks.download_images import download_images
from src.tasks.post_images import post_images
from src.tasks.update_subs import update_subs


def async_job(func):
    flag = Event()

    def _async():
        flag.set()
        func()
        flag.clear()

    def _func():
        if not flag.is_set():
            Thread(target=_async).start()
        else:
            print("Task locked, ignore:", func)

    return _func


schedule.every(17).minutes.do(async_job(update_subs))
schedule.every(13).minutes.do(async_job(update_index))
schedule.every(8).minutes.do(async_job(download_images))
schedule.every(5).minutes.do(async_job(post_images))
schedule.every(1).hours.do(async_job(clean_cache))


def run_schedule():
    connect_db()
    ItemInfo.clean_pending_items()
    async_job(update_subs)()
    async_job(update_index)()
    async_job(download_images)()
    async_job(post_images)()
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    run_schedule()
