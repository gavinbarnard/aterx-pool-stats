#!/usr/bin/env python

import ipaddress
from os.path import exists
from testlib.util import load_env, get_env_file

def test_env():
    env_dict = load_env(get_env_file())
    config_items = [
        "git_repo",
        "test_path",
        "monerod_ip",
        "monerod_rpc_port",
        "wallet_rpc_ip",
        "wallet_rpc_port",
        "wallet_file",
        "wallet_password",
        "nettype",
        "test_pool_port",
        "test_pool_webui_port",
        "test_pool_wallet_address",
        "test_pool_fee_wallet_address",
        "test_build_dir"
    ]
    for key in config_items:
        assert key in env_dict.keys()
    assert isinstance(env_dict['nettype'], str)
    assert env_dict['nettype'] in ['mainnet', 'stagenet', 'testnet']
    int_list = [
        'wallet_rpc_port',
        'monerod_rpc_port',
        'test_pool_port',
        'test_pool_webui_port'
    ]
    ip_list = [
        'monerod_ip',
        'wallet_rpc_ip',
    ]
    str_list = [
        'git_repo',
        'test_path',
        'test_pool_wallet_address',
        'test_pool_fee_wallet_address'
    ]
    for key in int_list:
        assert isinstance(int(env_dict[key]), int)
    for key in ip_list:
        try:
            ipaddress.ip_address(env_dict[key])
        except ipaddress.AddressValueError as e:
            assert True
    for key in str_list:
        assert isinstance(env_dict[key], str)
    test_path = env_dict['test_path']
    assert exists(test_path)
    
