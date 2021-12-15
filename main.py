import sys

from scheduled_tasks import run_schedule
from src.models.connect import connect_db
from src.tasks.clean_cache import clean_cache
from src.tasks.download_images import download_images
from src.tasks.post_images import post_images
from src.tasks.server import launch
from src.tasks.update_index import update_index
from src.tasks.update_subs import update_subs


def main():
    cmd = sys.argv[1]
    if cmd == 'server':
        launch()
    elif cmd == 'cron':
        task = sys.argv[2]
        run_schedule(task)
    elif cmd == 'update_subs':
        connect_db()
        update_subs()
    elif cmd == 'update_index':
        connect_db()
        update_index()
    elif cmd == 'download_images':
        connect_db()
        download_images()
    elif cmd == 'post_images':
        connect_db()
        post_images()
    elif cmd == 'clean_cache':
        connect_db()
        clean_cache()
    else:
        print("WTF??")

if __name__ == '__main__':
    main()
