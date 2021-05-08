#!/bin/sh
# -*- coding: utf-8 -*-

CONFIG_FILE=~/pool-stats.conf

jq . $CONFIG_FILE > /dev/null

if [ $? != 0 ];
then
        echo '{"error": "bad config"}'
        exit;
fi

blocks_file=`jq -r .block_inout $CONFIG_FILE`
IP=localhost
PORT=18081
echo "["
first=""
for i in `grep "UNLOCKED" $blocks_file | awk '{print $1}' | tac`
do
	echo $first
	first=","
	if [ ! -f /tmp/$i ]; then
		curl -s http://$IP:$PORT/json_rpc -d '{"jsonrpc":"2.0","id":"0","method":"get_block", "params": { "height": '$i' }}' > /tmp/$i
	fi
	if [ -f /tmp/$i ]; then
		height=$i
		ts=`jq -r .result.block_header.timestamp /tmp/$i`
		amount=`jq -r .result.block_header.reward /tmp/$i`
		echo '{"height": '$i', "timestamp": '$ts', "reward": '$amount','
	fi
	effort=null
	for l in /home/monero/blocks-records/*.json
	do
		nheight=$(($height-1))
		theigh=`jq -r .network_height $l`
		if [ "$nheight" -eq "$theigh" ]; then
			rhash=`jq -r .round_hashes $l`
			nhash=`jq -r .network_hashrate $l`
			effort=$(($rhash/$nhash))
		fi
	done
	echo '"effort": '$effort
	echo "}"
done
echo "]"


