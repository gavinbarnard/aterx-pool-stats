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
            'inspect',  # path to inspect-data
            'pooldd',   # path to pool data dir
            'sitename', # Site name to use inside templte
            'template_html', # path to template html file
            'pool_html', # path to output html file
            'stats_dir', # path to store last 900 minutes of JSON data
            'stats_out', # path to stats_out/graph_stats.json see sample.nginx.conf
            'multi_out', # used for reporting the nearest 1:10^n ratio on graph
            'average_out', # average hash rate out file 
            'block_find_out', # file stating the amount of blocks you should find in 30 days
            'block_inout', # file to dump to with inspect data, and include in template build
            'site_ip', # endpoint to get stats from
            'script_dir', # where these scripts are located
            'pool_logo', # pool logo file
            'payout_file' # where to store payout json
        ]
        for key in config_keys:
            if key not in config.keys():
                sys.stderr.write("missing config key {}".format(key))
                exit(1)
    else:
        sys.stderr.write("error reading config file {}".format(config_file))
        exit(1)
    return config
