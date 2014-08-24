import logging
import itertools
from datetime import datetime

import requests
import requests.exceptions
from requests.adapters import HTTPAdapter
from pymongo import MongoClient
from celery import Celery, task, group
from celery.utils.log import get_task_logger

from ..config import MONGO_URI, API_URL, API_TOKEN, API_REQUEST_TIMEOUT, \
    CELERY_BROKER_URL, CELERY_RESULT_BACKEND


s = requests.Session()
s.mount(API_URL, HTTPAdapter(max_retries=5))

celery = Celery('history-sync', broker=CELERY_BROKER_URL)
celery.conf.update({'CELERY_RESULT_BACKEND': CELERY_RESULT_BACKEND})

logger = get_task_logger(__name__)
logger.setLevel(logging.INFO)

client = MongoClient(MONGO_URI)
db = client['clan_history']
db_clans = db['clans']
db_players = db['players']

db_clans.ensure_index('member_ids')
db_players.ensure_index('account_name')


def sync():
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.StreamHandler())
    res = group(get_clans.s(no) for no in range(107, 200))().get()
    clans = list(itertools.chain.from_iterable(res))
    num_players = sum(clan['members_count'] for clan in clans)
    logger.info("Processing %d clans and %d players in total", len(clans), num_players)
    group([get_members_and_update_db.s(clan) for clan in clans])().get()
    logger.info("Checking players that are not in any clans")
    for player in db_players.find():
        if db_clans.find_one({'member_ids': player['account_id']}, {"_id": 1}) is None:
            player['has_clan'] = False
            db_players.update({'_id': player['_id']}, player)


def update_player(clan_info, player_info):
    account_id = player_info['account_id']
    player = db_players.find_one({'_id': account_id})
    if player is None:
        logger.info('Inserting new player \'%d\'', account_id)
        player = {
            '_id': account_id,
            'has_clan': True,
            'account_id': account_id,
            'account_name': player_info['account_name'],
            'history': [
                {
                    'clan_id': clan_info['clan_id'],
                    'clan_name': clan_info['name'],
                    'created_at': datetime.utcfromtimestamp(player_info['created_at']),
                    'last_seen': datetime.utcnow()
                }
            ]
        }
    else:
        logger.info('Updating history of player \'%d\'', account_id)
        last = player['history'][-1]
        if not player['has_clan'] or last['clan_id'] != clan_info['clan_id']:
            # player clan changed, add history entry
            player['history'] += {
                'clan_id': clan_info['clan_id'],
                'clan_name': clan_info['name'],
                'created_at': datetime.utcfromtimestamp(player_info['created_at']),
                'last_seen': datetime.utcnow()
            }
        else:
            last['last_seen'] = datetime.utcnow()
        player['has_clan'] = True
    return player


@task(rate_limit='10/s')
def get_members_and_update_db(clan):
    logger.info("Getting members of clan '%s'", str(clan['name']))
    try:
        r = requests.get(API_URL + '/clan/info/', timeout=API_REQUEST_TIMEOUT,
                         params={
                             'application_id': API_TOKEN,
                             'clan_id': clan['clan_id']
                         })
        logger.info("Received members of clan '%s'", str(clan['name']))
        response = r.json()
        if r.status_code == 200 and response['status'] == 'ok':
            clan_info = response['data'][str(clan['clan_id'])]

            logger.info("Updating info of clan '%s'", str(clan_info['clan_id']))
            clan_info['_id'] = clan_info['clan_id']
            clan_info['member_ids'] = [member['account_id'] for member in clan_info['members'].values()]
            db_clans.update({"_id": clan_info['_id']}, clan_info, upsert=True)

            if len(clan_info["members"]) == 0:
                return

            bulk = db_players.initialize_unordered_bulk_op()
            for _, player_info in clan_info['members'].items():
                player = update_player(clan_info, player_info)
                bulk.find({'_id': player['_id']}).upsert().update({'$set': player})
            bulk.execute()
            logger.info("Executed bulk commands")

    except requests.exceptions.ConnectionError as e:
        logger.error("Connection error when trying to get members of clan '%s'", clan['name'])


@task(rate_limit='10/s')
def get_clans(page_no):
    logger.info("Getting clans page " + str(page_no))
    r = requests.get(API_URL + '/clan/list/', timeout=API_REQUEST_TIMEOUT,
                     params={
                         'application_id': API_TOKEN,
                         'page_no': page_no
                     })
    logger.info("Received clans page " + str(page_no))
    response = r.json()
    if r.status_code == 200 and response['status'] == 'ok':
        return [clan for clan in response['data']]
