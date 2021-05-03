#!/bin/sh

CONFIG_FILE=~/pool-stats.conf

jq . $CONFIG_FILE

if [ $? != 0 ];
then
	echo bad config
	exit;
fi

STATS_DIR=`jq -r .stats_dir $CONFIG_FILE`

find $STATS_DIR -name \*.json -mmin +910 -delete

export POOLDD=`jq -r .pooldd $CONFIG_FILE`
INSPECT=`jq -r .inspect $CONFIG_FILE`
blocks_file=`jq -r .block_inout $CONFIG_FILE`
site=`jq -r .site_ip $CONFIG_FILE`
script_dir=`jq -r .script_dir $CONFIG_FILE`
minerlist=`jq -r .minerlist $CONFIG_FILE`
payouts_dir=`jq -r .payout_info_dir $CONFIG_FILE` 

$INSPECT -p $POOLDD | awk '{print $1}' | sort | uniq > $minerlist

for i in `cat $minerlist`; do $INSPECT -p $POOLDD | grep "$i" | sed 's:\n:<br/>:' > $payouts_dir/$i; done

$INSPECT -m $POOLDD > $blocks_file
curl -s http://$site/stats > $STATS_DIR/latest-`date --iso-8601=seconds`.json
find $STATS_DIR -name \*.json -size -300c -delete # removes broken stats files
$script_dir/get_transfers.sh | jq .result.out > `jq -r .payout_file $CONFIG_FILE`
python $script_dir/stats.py -c $CONFIG_FILE
python $script_dir/report.py -c $CONFIG_FILE
