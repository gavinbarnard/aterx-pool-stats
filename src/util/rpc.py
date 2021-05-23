import json
import requests
from operator import itemgetter

def monerod_get_block(rpc_port, block_height):
    # {"jsonrpc":"2.0","id":"0","method":"get_block", 
    # "params": { "height": '$i' }}
    data = {
        "jsonrpc":"2.0",
        "id":"0",
        "method":"get_block",
        "params": {"height": block_height}
    }
    r = requests.post("http://localhost:{}/json_rpc".format(rpc_port), data=json.dumps(data))
    r.raise_for_status()
    return r.json()['result']

def monerod_get_height(rpc_port):
    r = requests.get("http://localhost:{}/get_info".format(rpc_port))
    r.raise_for_status()
    return r.json()['height']

def moneropool_get_stats(site_ip):
    r = requests.get("http://{}/stats".format(site_ip))
    r.raise_for_status()
    return r.json()

def wallet_get_transfers_out(rpc_port):
    data = {
        "jsonrpc":"2.0",
        "id":"0",
        "method": "get_transfers",
        "params": {
            "in": False,
            "out": True,
            "pending": False,
            "failed": False,
            "pool": False
        }
    }
    r = requests.get("http://localhost:{}/json_rpc".format(rpc_port), data=json.dumps(data))
    r.raise_for_status()
    out_dict = sorted(r.json()['result']['out'], key=itemgetter('timestamp'), reverse=True)
    return out_dict