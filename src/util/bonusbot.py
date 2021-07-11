import json
from util.moneropooldb import get_balance
from util.rpc import moneropool_get_stats
from util.config import parse_config, cli_options

config_items = parse_config(cli_options())
pooldd = config_items['pooldd']

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
    return addresses

print(get_miner_pool())
