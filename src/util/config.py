import os
import json
import argparse
import sys


def cli_options():
    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--config", action="store", default=os.environ['HOME'] + "/pool-stats.conf")
    args = ap.parse_args()
    if args.config:
        return args.config
    else:
        ap.print_help()
        exit(1)

def parse_config(config_file):
    if os.path.isfile(config_file):
        config = json.loads(open(config_file,'r').read())
        config_keys = [
            'pooldd',   # path to pool data dir
            'sitename', # Site name to use inside templte
            'stats_dir', #path to store stats files
            'v0_template_html', # path to template html file
            'site_ip', # endpoint to get stats from
            'script_dir', # where path to the /src/ dir these scripts are located
            'pool_logo', # pool logo file
            'block_records', # path to dir of stat files before block hits
            'monerod_rpc_port', # monerod rpc port
            'monerod_ip', #monerod ip
            'monero_wallet_rpc_port'
        ]
        for key in config_keys:
            if key not in config.keys():
                sys.stderr.write("missing config key {}".format(key))
                raise(KeyError("missing configuration key {}".format(key)))
                exit(1)
    else:
        sys.stderr.write("error reading config file {}".format(config_file))
        exit(1)
    return config
