import sys

from scheduled_tasks import run_schedule
from src.tasks.download_images import download_images
from src.tasks.post_images import post_images
from src.tasks.server import launch
from src.tasks.update_index import update_index


def main():
    cmd = sys.argv[1]
    if cmd == 'server':
        launch()
    elif cmd == 'cron':
        run_schedule()
    elif cmd == 'update_index':
        update_index()
    elif cmd == 'download_images':
        download_images()
    elif cmd == 'post_images':
        post_images()
    else:
        print("WTF??")

if __name__ == '__main__':
    main()
