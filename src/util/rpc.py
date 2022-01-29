import json
import requests
from operator import itemgetter

def monerod_get_block(rpc_port, block_height, site="localhost"):
    # {"jsonrpc":"2.0","id":"0","method":"get_block", 
    # "params": { "height": '$i' }}
    data = {
        "jsonrpc":"2.0",
        "id":"0",
        "method":"get_block",
        "params": {"height": block_height}
    }
    r = requests.post("http://{}:{}/json_rpc".format(site, rpc_port), data=json.dumps(data))
    r.raise_for_status()
    return r.json()['result']

def monerod_get_height(rpc_port, site="localhost"):
    r = requests.get("http://{}:{}/get_info".format(site, rpc_port))
    r.raise_for_status()
    return r.json()['height']

def moneropool_get_stats(site_ip, wa=None, ssl=False):
    cookies = None
    if (wa):
        cookies = {}
        cookies['wa'] = wa
    if ssl:
        r = requests.get("https://{}/stats".format(site_ip), cookies=cookies)
    else:
        r = requests.get("http://{}/stats".format(site_ip), cookies=cookies)
    r.raise_for_status()
    return r.json()

def wallet_get_transfers_out(rpc_port, site="localhost"):
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
    r = requests.get("http://{}:{}/json_rpc".format(site, rpc_port), data=json.dumps(data))
    r.raise_for_status()
    out_dict = {}
    if "result" in r.json().keys():
        if "out" in r.json()['result'].keys():
            out_dict = sorted(r.json()['result']['out'], key=itemgetter('timestamp'), reverse=True)
    return out_dict[:30]

def wallet_get_pending_out_failed_tx(rpc_port, site="localhost"):
    data = {
        "jsonrpc":"2.0",
        "id":"0",
        "method": "get_transfers",
        "params": {
            "out": True,
            "pending": True,
            "in": False,
            "failed": True,
            "pool": False
        }
    }
    r = requests.get("http://{}:{}/json_rpc".format(site, rpc_port), data=json.dumps(data))
    r.raise_for_status()
    output = {}
    output['out'] = {}
    output['failed'] = {}
    output['pending'] = {}
    if "result" in r.json().keys():
        for n in ['out', 'failed', 'pending']:
            if n in r.json()['result'].keys():
                output[n] = sorted(r.json()['result'][n], key=itemgetter('timestamp'), reverse=True)
    return output

def wallet_get_tx_id(tx_id: str, rpc_port: int, site="localhost"):
    data = {
        "jsonrpc":"2.0",
        "id":"0",
        "method": "get_transfer_by_txid",
        "params": {
            "txid": tx_id,
        }
    }
    r = requests.post("http://{}:{}/json_rpc".format(site, rpc_port), data=json.dumps(data))
    r.raise_for_status()
    return r.json()

def wallet_get_balance(rpc_port: int, site="localhost"):
    data = {
        "jsonrpc":"2.0",
        "id":"0",
        "method": "get_balance"
    }
    r = requests.post("http://{}:{}/json_rpc".format(site, rpc_port), data=json.dumps(data))
    r.raise_for_status()
    return r.json()