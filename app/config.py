from sys import argv
from envparse import env
from dotenv import load_dotenv

load_dotenv()
DEBUG = not (len(argv) > 1 and argv[1] == '-O')

MYSQL_HOST = env.str('MYSQL_HOST', default='localhost')
MYSQL_PORT = env.int('MYSQL_PORT', default=3306)
MYSQL_PASSWORD = env.str('MYSQL_PASSWORD', default='')
MYSQL_USER = env.str('MYSQL_USER', default='')
MYSQL_DB = env.str('MYSQL_DB', default='')

REDIS_HOST = env.str('REDIS_HOST', default='localhost')
REDIS_PORT = env.int('REDIS_PORT', default=6379)
REDIS_DB = env.int('REDIS_DB', default=1)
CACHE_PREFIX = env.str('CACHE_PREFIX', default='')

APP_ID_MODE = env.bool('APP_ID_MODE', default=False)
APP_COUNT = env.int('APP_COUNT', default=1)
APP_ID = env.int('APP_ID', default=0)
