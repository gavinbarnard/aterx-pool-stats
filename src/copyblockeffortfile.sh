#!/bin/sh
CONFIG_FILE=~/pool-stats.conf

jq . $CONFIG_FILE > /dev/null
if [ $? != 0 ];
then
	echo bad config
	exit 1;
fi

block_records=`jq -r .block_records $CONFIG_FILE`
script_dir=`jq -r .script_dir $CONFIG_FILE`

effortfile=`$script_dir/getblockeffortfile.sh`
if [ $? != 0 ];
then
	echo "no block effort file detected"
	exit 0;
fi
lastfile=`ls $block_records/*.json | sort -r | head -1`

eblocks=`jq -r .pool_blocks_found $effortfile`
lblocks=`jq -r .pool_blocks_found $lastfile`

if [ "$eblocks" -eq "$lblocks" ]; then
	echo "Same old block"
else
	echo "New Block"
	num=`echo $lastfile | sed 's:/home/monero/blocks-records/::' | sed 's:.json::'`
	num=$(($num+1))
	cp $effortfile /home/monero/blocks-records/$num.json
fi
