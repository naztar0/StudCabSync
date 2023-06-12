#!/usr/bin/env python
import logging
from app import config
from app.utils import syncers
from app.utils import utils
from time import sleep


def sync(user):
    logging.debug(f'Syncing user {user.id}')
    user_api = utils.get_user_profile(user)
    if not user_api:
        logging.debug(f'User {user.id} not found in API')
        return
    logging.debug(f'Syncing profile {user_api}')
    syncers.sync_profile(user, user_api)
    logging.debug('Syncing syllabus')
    syncers.sync_syllabus(user)
    logging.debug('Syncing record book')
    syncers.sync_record_book(user)
    logging.debug('Syncing rating')
    syncers.sync_rating(user)
    if user.payment == 'contract':
        logging.debug('Syncing payments')
        syncers.sync_payments(user)


def run(app_id):
    users_per_app = utils.get_users_count() // config.APP_COUNT
    logging.debug(f'Users per app: {users_per_app}')
    if config.APP_ID_MODE:
        offset = users_per_app * config.APP_ID
    else:
        offset = users_per_app * app_id

    logging.debug(f'Offset: {offset}')

    chunk = 0
    chunk_size = 100

    while chunk < users_per_app:
        logging.debug(f'Syncing users {offset + chunk} - {offset + chunk + chunk_size}')
        users = utils.get_users(count=chunk_size, offset=offset + chunk)
        chunk += chunk_size
        for user in users:
            sync(user)


def loop(app_id=None):
    while True:
        run(app_id)
        sleep(60)
