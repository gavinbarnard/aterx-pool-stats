#!/bin/bash

source ~grb/aterx-pool-stats-env/bin/activate
cd /home/monero/aterx-pool-stats/src
python pplns_update.py
