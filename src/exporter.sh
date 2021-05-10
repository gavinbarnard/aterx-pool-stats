#!/bin/sh

CONFIG_FILE=~/pool-stats.conf

jq . $CONFIG_FILE

if [ $? != 0 ];
then
	echo bad config
	exit;
fi

STATS_DIR=`jq -r .stats_dir $CONFIG_FILE`
site=`jq -r .site_ip $CONFIG_FILE`
script_dir=`jq -r .script_dir $CONFIG_FILE`
find $STATS_DIR -name \*.json -mmin +910 -delete
$script_dir/copyblockeffortfile.sh
curl -s http://$site/stats > $STATS_DIR/latest-`date --iso-8601=seconds`.json
find $STATS_DIR -name \*.json -size -300c -delete # removes broken stats files
