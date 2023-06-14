#!/usr/bin/env python
import logging
from app import config
from app.utils import syncers
from app.utils import utils
from time import sleep


def sync(user, app_id):
    syncer = syncers.Syncers(app_id, user)
    logging.debug(f'Syncing user {user.id}')
    if not syncer.sync_profile():
        logging.debug(f'User {user.id} not found in API')
        return
    logging.debug('Syncing syllabus')
    syncer.sync_syllabus()
    logging.debug('Syncing record book')
    syncer.sync_record_book()
    logging.debug('Syncing rating')
    syncer.sync_rating()
    if user.payment == 'contract':
        logging.debug('Syncing payments')
        syncer.sync_payments()


def run(app_id):
    users_per_app = utils.get_users_count() // config.APP_COUNT
    logging.debug(f'Users per app: {users_per_app}')
    if config.APP_ID_MODE:
        app_id = config.APP_ID
    offset = users_per_app * app_id

    logging.debug(f'Offset: {offset}')

    chunk = 0
    chunk_size = 100

    while chunk < users_per_app:
        logging.debug(f'Syncing users {offset + chunk} - {offset + chunk + chunk_size}')
        users = utils.get_users(count=chunk_size, offset=offset + chunk)
        chunk += chunk_size
        for user in users:
            sync(user, app_id)


def loop(app_id=None):
    while True:
        run(app_id)
        sleep(60)
