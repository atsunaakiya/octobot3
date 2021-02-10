import time
from threading import Thread

import schedule

from src.models.connect import connect_db
from src.tasks.update_index import update_index
from src.tasks.download_images import download_images
from src.tasks.post_images import post_images
from src.tasks.update_subs import update_subs


def async_job(func):
    def _func():
        Thread(target=func).start()
    return _func


schedule.every(17).minutes.do(async_job(update_subs))
schedule.every(13).minutes.do(async_job(update_index))
schedule.every(8).minutes.do(async_job(download_images))
schedule.every(5).minutes.do(async_job(post_images))

def run_schedule():
    connect_db()
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    run_schedule()
