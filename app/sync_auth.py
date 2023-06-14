#!/usr/bin/env python
import logging
from app import config
from app.utils import utils
from app.utils import syncers
from app.utils.user_register import register_user
from app.utils.database_connection import DatabaseConnection
import redis
from time import sleep


def run():
    cache = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB)
    keys = cache.keys(config.CACHE_PREFIX + 'auth:*')
    for key in keys:
        logging.debug(f'Validating {key}')
        validated_and_incorrect = int(cache.get(key).decode())
        if validated_and_incorrect:
            continue
        *_, email, password = key.decode()[len(config.CACHE_PREFIX):].split(':')
        user_api = utils.api_request({'email': email, 'pass': password, 'page': 1})
        logging.debug(f'User: {user_api}')
        if not user_api:
            cache.set(key, 1, ex=60)
            continue
        with DatabaseConnection() as db:
            conn, cursor = db
            cursor.execute("SELECT id FROM users WHERE student_id=(%s) AND pass IS NULL AND azure_id IS NOT NULL", [user_api['st_cod']])
            user_id = cursor.fetchone()
            user_id = user_id[0] if user_id else None
            if user_id:
                cursor.execute("UPDATE users SET pass=(%s) WHERE id=(%s)", [(password, user_id)])
                conn.commit()
        if not user_id:
            logging.debug('Registering user')
            user_id = register_user(user_api, email, password)
        user = utils.get_user(user_id)
        syncer = syncers.Syncers(0, user)
        logging.debug('Syncing syllabus')
        syncer.sync_syllabus()
        logging.debug('Syncing record book')
        syncer.sync_record_book()
        logging.debug('Syncing rating')
        syncer.sync_rating()
        if user.payment == 'contract':
            logging.debug('Syncing payments')
            syncer.sync_payments()
        cache.delete(key)


def loop():
    while True:
        run()
        sleep(1)
