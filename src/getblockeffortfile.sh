#/bin/sh
CONFIG_FILE=~/pool-stats.conf

jq . $CONFIG_FILE > /dev/null
if [ $? != 0 ];
then
	echo bad config
	exit 1;
fi
stats_dir=`jq -r .stats_dir $CONFIG_FILE`
script_dir=`jq -r .script_dir $CONFIG_FILE`
for i in `egrep -ho '"pool_blocks_found":[0-9]*' $stats_dir/latest*.json | sort -t':' -n -k 2 | uniq`; do stat_file=`grep -l $i $stats_dir/latest*.json | tail -1`; echo $stat_file; done | wc -l > /tmp/block_effect_check
block_diff=`cat /tmp/block_effect_check`
if [ "$block_diff" -gt "1" ]; then
    for i in `egrep -ho '"pool_blocks_found":[0-9]*' $stats_dir/latest*.json | sort -t':' -n -k 2 | uniq`; do stat_file=`grep -l $i $stats_dir/latest*.json | tail -1`; echo $stat_file; done | head -1
else
    exit 1;
fi
