import sys

from src.enums import ServiceType
from src.models.connect import connect_db
from src.models.subscribe import SubscribeSource


def next_line():
    try:
        val = input().strip()
    except EOFError:
        return None
    else:
        return val


def main():
    connect_db()
    service, func, channel = sys.argv[1:]
    service = ServiceType(service)
    line = next_line()
    while line:
        SubscribeSource.add_subs(service, func, line, channel)
        line = next_line()


if __name__ == '__main__':
    main()
