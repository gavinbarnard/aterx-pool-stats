import json
from pymemcache.client import base

from datetime import datetime
from util.config import parse_config, cli_options
from util.moneropooldb import get_pplns_window_estimate

VERSION_PREFIX = "/0/"
config_items = parse_config(cli_options())
pooldd = config_items['pooldd']

def json_generic_response(generic_item):
    contype = "application/json"
    body = json.dumps(generic_item, indent=True)
    return contype, body

def json_pplns_estimate():
    pplns_est = get_pplns_window_estimate(config_items['pooldd'])
    return json_generic_response({"pplns_end":pplns_est})

def pplns_estimate_with_rewards():
    pplns_est, rewards =  get_pplns_window_estimate(config_items['pooldd'], True)
    return pplns_est, rewards

memcache_client = base.Client(('localhost',11211))
pplns_est, rewards = pplns_estimate_with_rewards()
contype, body = json_generic_response({"pplns_end":pplns_est})
request_uri = "{}pplns_est".format(VERSION_PREFIX)

memcache_client.set("{}_last".format(request_uri), json.dumps([datetime.now().timestamp()]))
memcache_client.set("{}_contype".format(request_uri), json.dumps([contype]))
memcache_client.set("{}_body".format(request_uri), json.dumps([body]))
for rewardkey in rewards.keys():
    r = json.dumps({"reward": rewards[rewardkey]}, indent=True)
    memcache_client.set("reward_{}".format(rewardkey), r)
