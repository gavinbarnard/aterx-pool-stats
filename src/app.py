import json
from glob import glob
from math import floor
from datetime import datetime
from pymemcache.client import base
from os.path import exists

from util.config import parse_config, cli_options
from util.moneropooldb import get_mined, get_payments, get_pplns_window_estimate
from util.cookiecutter import cookiecutter
from util.rpc import monerod_get_block, monerod_get_height, moneropool_get_stats, wallet_get_transfers_out
from bonusbot import get_latest_winner

VERSION_PREFIX = "/0/"
config_items = parse_config(cli_options())
pooldd = config_items['pooldd']


def data_gif():
    contype = "image/gif"
    gif = ""
    if exists("data.gif"):
        with open("data.gif", 'rb') as fh:
            gif = fh.read()
    return contype, gif

def pool_page():
    contype = "text/html"
    html = ""
    if (exists(config_items['v0_template_html'])):
        with open(config_items['v0_template_html'], 'r') as fh:
            html = fh.read()
        html = html.replace("<!-- SITENAME --!>", config_items['sitename'])
        html = html.replace("<!-- POOL_LOGO --!>", config_items['pool_logo'])
    return contype, html

def block_page(block):
    contype = "text/html"
    html = ""
    block_data = "<table>"
    monero_block = monerod_get_block(config_items['monerod_rpc_port'], block, config_items['monerod_ip'])
    for k in monero_block.keys():
        if k == "block_header":
            block_data = block_data + "<tr><td>block_header</td><td><table>"
            for bd in monero_block[k].keys():
                block_data = block_data + "<tr><td>{}</td><td>{}</td></tr>".format(bd,json.dumps(monero_block[k][bd], indent=True))
            block_data = block_data + "</table></td></tr>"
        elif k == "json":
            block_data = block_data + "<tr><td>json</td><td><table>"
            bd_json = json.loads(monero_block[k])
            for bd in bd_json.keys():
                if bd == "miner_tx":
                    block_data = block_data + "<tr><td>miner_tx</td><td><table>"
                    for tx in bd_json[bd].keys():
                        block_data = block_data + "<tr><td>{}</td><td>{}</td></tr>".format(tx, json.dumps(bd_json[bd][tx], indent=True))
                    block_data = block_data + "</table></td></tr>"
                else:
                    block_data = block_data + "<tr><td>{}</td><td>{}</td></tr>".format(bd,json.dumps(bd_json[bd], indent=True))
            block_data = block_data + "</table></td></tr>"
        else:
            block_data = block_data + "<tr><td>{}</td><td><pre>{}</pre></td></tr>".format(k,json.dumps(monero_block[k], indent=True))
    block_data = block_data + "</table>"
    if (exists("block.template.html")):
        with open("block.template.html", 'r') as fh:
            html = fh.read()
        html = html.replace("<!-- SITENAME --!>", config_items['sitename'])
        html = html.replace("<!-- POOL_LOGO --!>", config_items['pool_logo'])
        html = html.replace("<!-- BLOCKDATA --!>", block_data)
    return contype, html

def blockui_page():
    contype = "text/html"
    html = ""
    if (exists("blockui.template.html")):
        with open("blockui.template.html", 'r') as fh:
            html = fh.read()
        html = html.replace("<!-- SITENAME --!>", config_items['sitename'])
        html = html.replace("<!-- POOL_LOGO --!>", config_items['pool_logo'])
    return contype, html

def json_pplns_estimate():
    pplns_est = get_pplns_window_estimate(config_items['pooldd'])
    return json_generic_response({"pplns_end":pplns_est})

def json_graph_stats():
    stat_array = []
    highest_p = 0
    highest_n = 0
    lowest_p = -1
    files = get_files(config_items['stats_dir'] + "/*.json")
    stat_data = read_files(files)
    sorted_keys = sorted(stat_data)
    # make sure we only have the latest 900 items
    if len(sorted_keys) > 900:
        sorted_keys = sorted_keys[-900:]
    p = 0
    p_sum = 0
    # find the highest value to determine the graph percential
    for my_item in sorted_keys:
        p_sum += stat_data[my_item]['pr']
        p += 1
        if stat_data[my_item]['nr'] > highest_n:
            highest_n = stat_data[my_item]['nr']
        if stat_data[my_item]['pr'] > highest_p:
            highest_p = stat_data[my_item]['pr']
        if stat_data[my_item]['pr'] < lowest_p or lowest_p == -1:
            lowest_p = stat_data[my_item]['pr']
    if ( p != 0 ):
        p_avg = floor(p_sum / p)
    else:
        p_avg = 0
    if highest_n != 0:
        pp = highest_p / highest_n
    else:
        pp = 0
    if highest_p != 0: 
        p_avg_d = abs(floor(p_avg / (highest_p) * 150) - 150)
    else:
        p_avg_d = 149
    stat_array = []
    for my_item in sorted_keys:
        percentile = 0
        # the graph draws upside down so we invert the numbers
        percentile = abs(floor(stat_data[my_item]['nr'] / highest_n * 150) - 150)
        stat_data[my_item]['nrp'] = percentile
        percentile = 0
        if highest_p != 0:
            percentile = abs(floor(stat_data[my_item]['pr'] / (highest_p) * 150) - 150)
        else:
            percentile = 149
        stat_data[my_item]['prp'] = percentile
        stat_array.append(
                { 'nr':  stat_data[my_item]['nr'],
                  'pr':  stat_data[my_item]['pr'],
                  'nrp': stat_data[my_item]['nrp'],
                  'prp': stat_data[my_item]['prp'],
                  'nd': stat_data[my_item]['nd'],
                  'pavg': p_avg_d,
                  'ts': my_item
                  })
    return json_generic_response(stat_array)

def json_get_multi():
    response={}
    response['multi'] = 0
    pool_stats = moneropool_get_stats(config_items['site_ip'])
    pp = pool_stats['pool_hashrate'] / pool_stats['network_hashrate']
    for i in range(0,20):
        multi = 10**i
        if multi * pp > 1:
            break
    response['multi'] = multi
    return json_generic_response(response)

def json_payments_summary():
    response = []
    payments = wallet_get_transfers_out(config_items['monero_wallet_rpc_port'])
    for payment in payments:
        bb={}
        bb['reward'] = payment['amount']
        if "destinations" in payment:
            bb['miner_count'] = len(payment['destinations'])
        else:
            bb['miner_count'] = 'Unknown'
        bb['timestamp'] = payment['timestamp']
        response.append(bb)
    return json_generic_response(response)

def json_blocks_all_really_response():
    effort_data = {}
    final_blocks = []
    pool_blocks = get_mined(pooldd)
    block_records = glob("{}/*".format(config_items['block_records']))
    net_height = monerod_get_height(config_items['monerod_rpc_port'], config_items['monerod_ip'])
    for block in block_records:
        with open(block, 'r') as fh:
            block_d = fh.read()
        b = json.loads(block_d)
        effort_data[b['height']] = b
    for block in pool_blocks:
        real_block = monerod_get_block(config_items['monerod_rpc_port'], block['height'], config_items['monerod_ip'])
        if block['height'] in effort_data.keys():
            if effort_data[block['height']]['round_hashes'] != 0:
                effort = effort_data[block['height']]['round_hashes']/effort_data[block['height']]['network_difficulty'] * 100
                effort = round(effort, 2)
            else:
                effort = 0
        else:
            effort = 0
        bb = {}
        bb['height'] = block['height']
        bb['timestamp'] = real_block['block_header']['timestamp']
        bb['reward'] = real_block['block_header']['reward']
        if block['status'] == "ORPHANED":
            bb['reward'] = 0
        bb['effort'] = effort
        bb['status'] = block['status']
        json_inside_json = json.loads(real_block['json'])
        bb['hash_match'] = False
        if block['hash'].encode('utf-8') == real_block['block_header']['hash'].encode('utf-8'):
            bb['hash_match'] = True
        bb['unlock_height'] = json_inside_json['miner_tx']['unlock_time']
        bb['blocks_to_unlock'] = bb['unlock_height'] - net_height + 1
        if bb['blocks_to_unlock'] < 0:
            bb['blocks_to_unlock'] = 0
        final_blocks.append(bb)
    final_blocks.reverse()
    return json_generic_response(final_blocks)

def json_blocks_all_response():
    effort_data = {}
    final_blocks = []
    pool_blocks = get_mined(pooldd)
    block_records = glob("{}/*".format(config_items['block_records']))
    net_height = monerod_get_height(config_items['monerod_rpc_port'], config_items['monerod_ip'])
    for block in block_records:
        with open(block, 'r') as fh:
            block_d = fh.read()
        b = json.loads(block_d)
        effort_data[b['height']] = b
    for block in pool_blocks:
        real_block = monerod_get_block(config_items['monerod_rpc_port'], block['height'], config_items['monerod_ip'])
        if block['height'] in effort_data.keys():
            if effort_data[block['height']]['round_hashes'] != 0:
                effort = effort_data[block['height']]['round_hashes']/effort_data[block['height']]['network_difficulty'] * 100
                effort = round(effort, 2)
            else:
                effort = 0
        else:
            effort = 0
        bb = {}
        bb['height'] = block['height']
        bb['timestamp'] = real_block['block_header']['timestamp']
        bb['reward'] = real_block['block_header']['reward']
        if block['status'] == "ORPHANED":
            bb['reward'] = 0
        bb['effort'] = effort
        bb['status'] = block['status']
        json_inside_json = json.loads(real_block['json'])
        bb['hash_match'] = False
        if block['hash'].encode('utf-8') == real_block['block_header']['hash'].encode('utf-8'):
            bb['hash_match'] = True
        bb['unlock_height'] = json_inside_json['miner_tx']['unlock_time']
        bb['blocks_to_unlock'] = bb['unlock_height'] - net_height + 1
        if bb['blocks_to_unlock'] < 0:
            bb['blocks_to_unlock'] = 0
        final_blocks.append(bb)
    final_blocks.reverse()
    final_blocks = final_blocks[:30]
    return json_generic_response(final_blocks)

def json_blocks_response():
    effort_data = {}
    final_blocks = []
    net_height = monerod_get_height(config_items['monerod_rpc_port'], config_items['monerod_ip'])
    pool_blocks = get_mined(pooldd)
    block_records = glob("{}/*".format(config_items['block_records']))
    for block in block_records:
        with open(block, 'r') as fh:
            block_d = fh.read()
        b = json.loads(block_d)
        effort_data[b['height']] = b
    for block in pool_blocks:
        real_block = monerod_get_block(config_items['monerod_rpc_port'], block['height'], config_items['monerod_ip'])
        if block['height'] in effort_data.keys():
            if effort_data[block['height']]['round_hashes'] != 0:
                effort = effort_data[block['height']]['round_hashes']/effort_data[block['height']]['network_difficulty'] * 100
                effort = round(effort, 2)
            else:
                effort = 0
        else:
            effort = 0
        if block['status'] == "LOCKED":
            if block['hash'].encode('utf-8') == real_block['block_header']['hash'].encode('utf-8'):
                if net_height - block['height'] >= 5:
                    bb = {}
                    bb['height'] = block['height']
                    bb['timestamp'] = real_block['block_header']['timestamp']
                    bb['reward'] = real_block['block_header']['reward']
                    bb['effort'] = effort
                    bb['status'] = block['status']
                    final_blocks.append(bb)
        if block['status'] == "UNLOCKED":
            bb = {}
            bb['height'] = block['height']
            bb['timestamp'] = real_block['block_header']['timestamp']
            bb['reward'] = real_block['block_header']['reward']
            bb['effort'] = effort
            bb['status'] = block['status']
            final_blocks.append(bb)
    final_blocks.reverse()
    final_blocks = final_blocks[:30]
    return json_generic_response(final_blocks)

def json_generic_response(generic_item):
    contype = "application/json"
    body = json.dumps(generic_item, indent=True)
    return contype, body

def html_generic_response(generic_item):
    contype = "text/html"
    body = "<html><pre>{}</pre></html>".format(generic_item)
    return contype, body

def get_files(stats_files):
    files = glob(stats_files)
    return files

def read_files(files):
    response = {}
    dt_f = "%Y-%m-%dT%H:%M:%S"
    for filename in files:
        data = ""
        # 01234560123456789012345678
        # latest-2021-03-28T05:11:01+00:00.json
        latest_index = filename.index("latest")
        ts = filename[7+latest_index:26+latest_index]
        dt = datetime.strptime(ts, dt_f)
        ts = int(dt.timestamp())
        with open(filename,'r') as fh:
            data += fh.read()
        temp =  json.loads(data)
        response[ts] = {}
        response[ts]['pr'] = temp['pool_hashrate']
        response[ts]['nr'] = temp['network_hashrate']
        response[ts]['nd'] = temp['network_difficulty']
    return response

def application(environ, start_response):
    request_uri = environ['REQUEST_URI']
    if 'HTTP_COOKIE' in environ.keys():
        cookies = cookiecutter(environ['HTTP_COOKIE'])
        if 'wa' in cookies:
            wa = cookies['wa']
        else:
            wa = None
        if 'dark_mode' in cookies:
            dark_mode = cookies['dark_mode']
        else:
            dark_mode = False
    else:
        dark_mode = False
        wa = None
    parameters = {}
    if "?" in request_uri:
        splitter = request_uri.split("?")
        request_uri = splitter[0]
        parameters = splitter[1]
        print(parameters)
    if parameters:
        final_p = {}
        para_kv = parameters.split("&")
        for para in para_kv:
            k, v = para.split("=")
            final_p[k]=v
        parameters = final_p
    if len(request_uri) > 128:
        request_uri = request_uri[0:128]
    memcache_client = base.Client(('localhost',11211))
    last_api_time = memcache_client.get("{}_last".format(request_uri))
    usecache = False
    time_multi = 1
    if last_api_time == None:
        last_api_time = 0
    else:
        last_api_time = json.loads(last_api_time)[0]
    now = datetime.now().timestamp()
    if now - last_api_time > (30 * time_multi) or last_api_time == 0 or len(parameters) > 0:
        usecache = False
    else:
        usecache = True
    if "{}pplns_est".format(VERSION_PREFIX) == request_uri:
        usecache = True
    if "{}payments".format(VERSION_PREFIX) == request_uri:
        usecache = False
    if "{}blockui.html".format(VERSION_PREFIX) == request_uri:
        usecache = False
    contype = "text/plain"
    nothing = False
    
    # non parallel friendly! only let one thread do this at a time
    # this will update the memcache result for /0/pplns_est
    # this is the quickest way to make sure only 1 thread
    # executes this at a time.
    # schedule a cronjob to hit curl http://localhost:5252/local/0/pplns_est_generate
    # to update this do not expose this API to the world
    # may the spirits have mercy on you if you do
#    if "/local{}pplns_est_generate".format(VERSION_PREFIX) == request_uri:
#        contype, body = json_pplns_estimate()
#        request_uri = "{}pplns_est".format(VERSION_PREFIX)
#        memcache_client.set("{}_last".format(request_uri), json.dumps([datetime.now().timestamp()]))
#        memcache_client.set("{}_contype".format(request_uri), json.dumps([contype]))
#        memcache_client.set("{}_body".format(request_uri), json.dumps([body]))
    if not usecache:
        if VERSION_PREFIX == request_uri[0:len(VERSION_PREFIX)]:
            if "{}blocks".format(VERSION_PREFIX) == request_uri:
                contype, body = json_blocks_response()
            elif "{}blocks.all".format(VERSION_PREFIX) == request_uri:
                contype, body = json_blocks_all_response()
            elif "{}blocks.all.really".format(VERSION_PREFIX) == request_uri:
                contype, body = json_blocks_all_really_response()
            elif "{}payments".format(VERSION_PREFIX) == request_uri and len(wa) > 0:
                contype, body = json_generic_response(get_payments(pooldd, wa))
            elif "{}payments.summary".format(VERSION_PREFIX) == request_uri:
                contype, body = json_payments_summary()
            elif "{}multi".format(VERSION_PREFIX) == request_uri:
                contype, body = json_get_multi()
            elif "{}pool.html".format(VERSION_PREFIX) == request_uri:
                contype, body = pool_page()
            elif "{}blockui.html".format(VERSION_PREFIX) == request_uri:
                if parameters:
                    if "block" in parameters.keys():
                        contype, body = block_page(parameters['block'])
                else:
                    contype, body = blockui_page()
            elif "{}data.gif".format(VERSION_PREFIX) == request_uri:
                contype, body = data_gif()
            elif "{}graph_stats.json".format(VERSION_PREFIX) == request_uri:
                contype, body = json_graph_stats()
            elif "{}bonus_address".format(VERSION_PREFIX) == request_uri:
                response = get_latest_winner()
                contype, body = json_generic_response(response)
            else:
                contype, body = html_generic_response("I got nothing for you man!")
                nothing = True
        else:
            nothing = True
            body = "This should not be served"
        if not nothing and "{}payments".format(VERSION_PREFIX) != request_uri:
            memcache_client.set("{}_last".format(request_uri), json.dumps([datetime.now().timestamp()]))
            memcache_client.set("{}_contype".format(request_uri), json.dumps([contype]))
            memcache_client.set("{}_body".format(request_uri), json.dumps([body]))
    else:
        contype = memcache_client.get("{}_contype".format(request_uri))
        body = memcache_client.get("{}_body".format(request_uri))
        if contype and body:
            contype = json.loads(contype)[0]
            body = json.loads(body)[0]
        else:
            contype = "text/plain"
            body = "cache failure, deleted cache entries"
            memcache_client.delete("{}_last".format(request_uri))
            memcache_client.delete("{}_body".format(request_uri))
            memcache_client.delete("{}_contype".format(request_uri))
    start_response('200 OK', [('Content-Type', contype)])
    return [body.encode('utf-8')]
