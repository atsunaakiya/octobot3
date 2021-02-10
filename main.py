import sys

from scheduled_tasks import run_schedule
from src.tasks.server import launch


def main():
    cmd = sys.argv[1]
    if cmd == 'server':
        launch()
    elif cmd == 'cron':
        run_schedule()
    else:
        print("WTF??")

if __name__ == '__main__':
    main()
