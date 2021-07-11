#!/usr/bin/env python

'''
Copyright (c) 2018, The Monero Project

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation
and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors
may be used to endorse or promote products derived from this software without
specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''
# adapted from the inspect-data script in the monero-pool 
# https://github.com/jtgrassie/monero-pool/blob/master/tools/inspect-data
#
# pplns window payout based pool.c from monero-pool
# this chews i/o use sparingly
# and uses a payout value with 95% value of the last block
# with a share multipler of 2 currently as a fixed value
# https://github.com/jtgrassie/monero-pool/blob/master/src/pool.c#L923

import lmdb
from ctypes import *
from datetime import datetime
from math import floor

class share_t(Structure):
    _fields_ = [('height', c_longlong),
                ('difficulty', c_longlong),
                ('address', c_char*128),
                ('timestamp', c_longlong)]

class payment_t(Structure):
    _fields_ = [('amount', c_longlong),
                ('timestamp', c_longlong),
                ('address', c_char*128)]

class block_t(Structure):
    _fields_ = [('height', c_longlong),
                ('hash', c_char*64),
                ('prev_hash', c_char*64),
                ('difficulty', c_longlong),
                ('status', c_long),
                ('reward', c_longlong),
                ('timestamp', c_longlong)]

def format_block_hash(block_hash):
    return block_hash

def format_block_status(status):
    s = ["LOCKED", "UNLOCKED", "ORPHANED"]
    return s[status]

def format_timestamp(timestamp):
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def format_amount(amount):
    return '{0:.12f}'.format(amount/1e12)

def format_address(address):
    return address

def address_from_key(key):
    return key.decode('utf-8').rstrip('\0')

def get_balance(path, waddress=None):
    j = c_longlong.from_param(9999)
    response = []
    env = lmdb.open(path, readonly=True, max_dbs=1, create=False)
    balance = env.open_db('balance'.encode())
    with env.begin(db=balance) as txn:
        with txn.cursor() as curs:
            for key, value in curs:
                address = format_address(address_from_key(key))
                amount = c_longlong.from_buffer_copy(value).value
                amount = format_amount(amount)
                if waddress:
                    if waddress == address:
                        response.append(
                            {"address": address,
                            "amount": amount})
                        break
                else:
                        response.append(
                            {"address": address,
                            "amount": amount})
    env.close()
    return response

def get_payments(path, waddress=None):
    response = []
    env = lmdb.open(path, readonly=True, max_dbs=1, create=False)
    payments = env.open_db('payments'.encode())
    with env.begin(db=payments) as txn:
        with txn.cursor() as curs:
            for key, value in curs:
                address = address_from_key(key)
                p = payment_t.from_buffer_copy(value)
                amount = p.amount
                dt = p.timestamp
                if waddress:
                    if waddress == address:
                        response.append(
                            {"address": address[0:8],
                            "amount": amount,
                            "dt": dt })
                else:
                        response.append(
                            {"address": address[0:8],
                            "amount": amount,
                            "dt": dt })
    env.close()
    response.reverse()
    return response

def get_mined(path):
    response = []
    env = lmdb.open(path, readonly=True, max_dbs=1, create=False)
    blocks = env.open_db('blocks'.encode())
    with env.begin(db=blocks) as txn:
        with txn.cursor() as curs:
            for key, value in curs:
                height = c_longlong.from_buffer_copy(key).value
                b = block_t.from_buffer_copy(value)
                bh = format_block_hash(b.hash.decode('utf-8'))
                dt = b.timestamp
                difficulty = b.difficulty
                reward = b.reward
                status  = format_block_status(b.status)
                response.append(
                    {"height": height,
                    "hash": bh,
                    "status": status,
                    "difficulty": difficulty,
                    "reward": reward,
                    "dt": dt}
                )
    env.close()
    return response

def get_shares(path):
    response = []
    env = lmdb.open(path, readonly=True, max_dbs=1, create=False)
    shares = env.open_db('shares'.encode(), dupsort=True)
    with env.begin(db=shares) as txn:
        with txn.cursor() as curs:
            curs.last()
            for i in range(25):
                key, value = curs.item()
                height = c_longlong.from_buffer_copy(key).value
                share = share_t.from_buffer_copy(value)
                address = format_address(address_from_key(share.address))
                dt = format_timestamp(share.timestamp)
                response.append({
                    "height": height,
                    "address": address,
                    "dt": dt
                })
                if not curs.prev():
                    break
    env.close()
    return response

def get_pplns_window_estimate(path):
    # this chews i/os run sparringly
    blocks = get_mined(path)
    block = None
    for ublock in blocks:
        if ublock['status'] == "UNLOCKED":
            block = ublock
            break
    if not block:
        return 0
    env = lmdb.open(path, readonly=True, max_dbs=1, create=False)
    shares = env.open_db('shares'.encode(), dupsort=True)
    total_pay = 0
    # use 95% of the previous block reward to 'guess'
    block['reward'] = floor(.95 * block['reward'])
    with env.begin(db=shares) as txn:
        with txn.cursor() as curs:
            curs.last()
            while(1):
                key, value = curs.item()
                share = share_t.from_buffer_copy(value)
                dt = share.timestamp
                pay_amount = floor(share.difficulty / (block['difficulty'] * 2) * block['reward'])
                if (pay_amount + total_pay > block['reward']):
                    pay_amount = block['reward'] - total_pay
                total_pay += pay_amount
                if total_pay == block['reward']:
                    return dt
                if not curs.prev():
                    return dt

if __name__ == '__main__':
    pass

