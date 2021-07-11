import json
from util.moneropooldb import get_balance
from util.rpc import moneropool_get_stats
from util.config import parse_config, cli_options
from os.path import exists

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

print(json.dumps(get_miner_pool(), indent=True))
