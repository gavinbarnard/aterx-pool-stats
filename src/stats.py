# stats parser for jtgrassie pool

import json
import sys
import os
from glob import glob
from datetime import datetime
from math import floor

from util.config import parse_config, cli_options

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
    return response

def main():
    config_file = cli_options()
    config_items = parse_config(config_file)
    MULTI_FILE = config_items['multi_out']
    BLOCK_FIND_FILE = config_items['block_find_out']
    AVERAGE_FILE = config_items['average_out']
    STATS_FILES = config_items['stats_dir'] + "/*.json"
    STATS_OUT_FILE = config_items['stats_out']
    highest_p = 0
    highest_n = 0
    lowest_p = -1
    files = get_files(STATS_FILES)
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
    for i in range(0, 20):
        multi = 10**i
        if multi * pp > 1:
            break
    #calculate where in our graph data everything shoudl go in a 900 wide x 150 high image
    if highest_p != 0: 
        p_avg_d = abs(floor(p_avg / (highest_p-lowest_p) * 150) - 150)
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
            percentile = abs(floor(stat_data[my_item]['pr'] / (highest_p-lowest_p) * 150) - 150)
        else:
            percentile = 149
        stat_data[my_item]['prp'] = percentile
        stat_array.append(
                { 'nr':  stat_data[my_item]['nr'],
                  'pr':  stat_data[my_item]['pr'],
                  'nrp': stat_data[my_item]['nrp'],
                  'prp': stat_data[my_item]['prp'],
                  'pavg': p_avg_d,
                  'ts': my_item
                  })

    if highest_n != 0:
        block_chance = round(p_avg / highest_n * 30 * 24 * 30, 2)
    else:
        block_chance = 0

    block_fh = open(BLOCK_FIND_FILE, 'w')
    block_fh.write("At current average pool hashrate vs the highest observed network hashrate will hopefully {} blocks every 30 days".format(block_chance))
    block_fh.close()
    #write out the files
    stats_out_fh = open(STATS_OUT_FILE, 'w')
    stats_out_fh.write(json.dumps(stat_array))
    stats_out_fh.close()
    avg_fh = open(AVERAGE_FILE, 'w')
    avg_fh.write("{}".format(p_avg))
    avg_fh.close()
    multi_fh = open(MULTI_FILE, 'w')
    multi_fh.write("{}".format(multi))
    multi_fh.close()



if __name__ == "__main__":
    main()
