#!/usr/bin/env python

import json
from os.path import exists

from util.config import parse_config, cli_options
config_items = parse_config(cli_options())
pooldd = config_items['pooldd']

def log_scrape_mined_lines():
    log_file = config_items['poollog']
    mined_lines = []
    if exists(log_file):
        log_fh = open(log_file, 'r')
        file_line = "start"
        while file_line:
            file_line = log_fh.readline()
            if "+++ MINED A BLOCK +++" in file_line:
                mined_lines.append(file_line)
    return mined_lines

def extract_effort_data():
    block_records_path = config_items['block_records']
    mined_lines = log_scrape_mined_lines()
    for line in mined_lines:
        explosion = line.split(" ")
        miner = explosion[10].strip()
        roundhr = explosion[11].strip()
        nethr = explosion[13].strip()
        height = int(explosion[14].strip())+1
        test_file_name = "{}/{}".format(block_records_path, height)
        if not exists(test_file_name):
            block = {
                "miner": miner,
                "round_hashes": int(roundhr),
                "network_hashrate": int(nethr),
                "height": height
            }
            print("Found new block in log {}".format(height))
            fh = open(test_file_name, 'w')
            fh.write(json.dumps(block, indent=True))
            fh.close()


if __name__ == "__main__":
    extract_effort_data()