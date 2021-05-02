#!/bin/sh

IP=localhost
PORT=28084
METHOD="get_transfers"


curl -s http://$IP:$PORT/json_rpc -d '{"jsonrpc":"2.0","id":"0","method":"'$METHOD'", "params": {"in":true,"out":true,"pending":true,"failed":true,"pool":true,"account_index":0}}' -H "Content-Type: application/json"

echo
