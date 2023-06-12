#!/usr/bin/env python
import os
from app import config
from app import sync_users
from app import sync_auth


def main():
    if config.APP_ID_MODE:
        if config.APP_ID == 0:
            if os.fork() == 0:
                sync_auth.loop()
                exit()
        sync_users.loop()
        exit()
    if os.fork() == 0:
        sync_auth.loop()
        exit()
    for i in range(config.APP_COUNT):
        if os.fork() == 0:
            sync_users.loop(i)
            exit()


def debug():
    sync_users.loop()
    # sync_auth.loop()


if __name__ == '__main__':
    if config.DEBUG:
        debug()
    else:
        main()
