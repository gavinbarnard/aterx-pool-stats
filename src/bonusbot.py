import json
from time import time
from os.path import exists
from random import randint

from requests.api import get
from util.moneropooldb import get_balance
from util.rpc import moneropool_get_stats
from util.config import parse_config, cli_options

config_items = parse_config(cli_options())
pooldd = config_items['pooldd']

def load_bans():
    bans = None
    ban_file = "{}/bans.json".format(config_items['bonus_bot_path'])
    if exists(ban_file):
        with open(ban_file,'r') as fh:
            ban_contents = fh.read()
        bans = json.loads(ban_contents)
    return bans

def get_miner_pool():
    addresses = []
    all_balances = get_balance(pooldd)
    for miner in all_balances:
        stats = moneropool_get_stats(config_items['site_ip'], wa=miner['address'])
        if stats['connected_miners'] > 0 and (
            stats['miner_hashrate_stats'][0] > 0 or
            stats['miner_hashrate_stats'][1] > 0 or
            stats['miner_hashrate_stats'][2] > 0 or
            stats['miner_hashrate_stats'][3] > 0 or
            stats['miner_hashrate_stats'][4] > 0 or
            stats['miner_hashrate_stats'][5] > 0
            ):
            addresses.append(miner['address'])
    bans = load_bans()
    for ban in bans:
        if ban in addresses:
            addresses.remove(ban)
    return addresses

def get_winner_pool():
    winner_pool = []
    winner_file = "{}/winners.json".format(config_items['bonus_bot_path'])
    if exists(winner_file):
        with open(winner_file,'r') as fh:
            winner_content = fh.read()
        winner_pool = json.loads(winner_content)
    return winner_pool

def add_winner(wa=None):
    if (wa):
        winner_pool = get_winner_pool()
        dt = int(time())
        found = False
        for winner in winner_pool:
            if winner['address'] == wa:
                winner['wins'].append(dt)
                found = True
        if found == False:
            winner_pool.append({
                'address': wa,
                'wins': [dt]
            }
            )
        winner_file = "{}/winners.json".format(config_items['bonus_bot_path'])
        fh = open(winner_file, 'w')
        fh.write(json.dumps(winner_pool))

def get_latest_winner():
    winner_pool = get_winner_pool()
    latest_winner = ""
    dt = 0
    for winner in winner_pool:
        for windt in winner['wins']:
            if windt > dt:
                dt = windt
                latest_winner = winner['address']

def get_highest_win_count():
    winner_pool = get_winner_pool()
    highest_wins = 0
    for winner in winner_pool:
        if len(winner['wins']) > highest_wins:
            highest_wins = len(winner['wins'])
    return highest_wins

def reduce_draw_pool():
    miner_pool = get_miner_pool()
    winner_pool = get_winner_pool()
    winners = []
    for winner in winner_pool:
        winners.append(winner['address'])
    for miner in miner_pool:
        if miner not in winners:
            winner_pool.append({
                'address': miner,
                'wins': []
            })
    highest_wins = get_highest_win_count()
    remove_list = []
    for winner in winner_pool:
        if len(winner['wins']) >= highest_wins and highest_wins != 0:
            remove_list.append(winner)
    for winner in remove_list:
        winner_pool.remove(winner)
    return winner_pool


def pull_winner():
    draw_pool = reduce_draw_pool()
    max_rand = len(draw_pool)
    choice = randint(0, max_rand)
    winner = draw_pool[choice]
    add_winner(winner['address'])
    return get_latest_winner()


print(pull_winner())

print(pull_winner())