#!/bin/bash
CONFIG_FILE=~/pool-stats.conf

jq . $CONFIG_FILE

if [ $? != 0 ];
then
	echo bad config
	exit;
fi

VENV=`jq -r .venv $CONFIG_FILE`
SCRIPT_DIR=`jq -r .script_dir $CONFIG_FILE`
source $VENV/bin/activate
cd $SCRIPT_DIR 
python bonusbot.py
