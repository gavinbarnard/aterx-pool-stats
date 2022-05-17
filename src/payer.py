# payer routine for pool.aterx.com

import json
from uuid import uuid4
import requests
from enum import Enum
from time import sleep
from util.moneropooldb import db 
from util.rpc import wallet_get_tx_id, wallet_get_balance
import functools

THRESHOLD = int(0.005 * 1e12)
WALLET_PORT = 28094
DATA_DIR = "/tmp/testbuild/data-dir"
PAYOUT_DIR = "/home/monero/payout_dir"
DRY_RUN = False
EXCLUDE_LIST = ["73sEiFJyUN16wWDYvGDeCjD7XL46K77QBGomFSSARZ4vBMJ751m1hDGfDP6itx9vxcYGCX78sgN9sNzposqEyMFmCxNJgxr", "45U6ZRiAAHoHYCmnsYocaaFLaxFESAdcoCWTLhoi9zgm49cJrWaTci12D5QVEcwtiuMSsSSKs1paiFoAoegx8iNH633Z9nY"]

class PaymentState(Enum):
    QUEUE = 0
    PENDING = 1
    PAIDONCHAIN = 2
    SUCCESS = 3
    FAILED = 255

class PaymentAlreadyInTransaction(Exception):
    pass

class TransactionUnsent(Exception):
    pass

class TransactionFull(Exception):
    pass

class Payment(object):
    def __init__(self, to_wallet, amount):
        self.to_wallet = to_wallet
        self.addr = self.to_wallet
        self.amount = int(amount)

class Transaction(object):
    def __init__(self, state=PaymentState.QUEUE):
        self.payments = []
        self.amount = 0
        self.state = state
        self.tx_hash = None
        self.fail_count = 0
        self.fail_responses = []

    def _update_payment_state(self):
        if self.tx_hash and self.state == PaymentState.PENDING:
            tx = self.get_tx()
            pcount = 0
            ocount = 0
            fcount = 0
            if type(tx) == list:
                for txn in tx:
                    if "result" in txn.keys():
                        if "transfer" in txn['result'].keys():
                            if "type" in txn['result']['transfer'].keys():
                                if txn['result']['transfer']['type'] == "out":
                                    ocount += 1
                                elif txn['result']['transfer']['type'] == "failed":
                                    fcount += 1
                                    self.state = PaymentState.FAILED
                                elif txn['result']['transfer']['type'] == "pending":
                                    self.state = PaymentState.PENDING
                                    pcount += 1
                if ocount == len(self.tx_hash):
                    self.state = PaymentState.PAIDONCHAIN
            elif type(tx) == str:
                if "result" in tx.keys():
                    if "transfer" in tx['result'].keys():
                        if "type" in tx['result']['transfer'].keys():
                            if tx['result']['transfer']['type'] == "out":
                                self.state = PaymentState.PAIDONCHAIN
                            elif tx['result']['transfer']['type'] == "failed":
                                self.state = PaymentState.FAILED
                            elif tx['result']['transfer']['type'] == "pending":
                                self.state = PaymentState.PENDING

    def add_payment(self, payment: Payment):
        #if len(self.payments) >= 15:
        #    raise TransactionFull
        if payment not in self.payments:
            self.payments.append(payment)
        else:
            raise PaymentAlreadyInTransaction

    def build_transfer_data(self):
        data = {
            "jsonrpc": "2.0",
            "id": "0",
            "method": "transfer_split",
            "params": 
            {
                "destinations": []
            }
        }
        for pay in self.payments:
            data['params']['destinations'].append(
                {"address": pay.to_wallet, "amount": pay.amount}
            )
        return data

    def send_tx_to_wallet_rpc(self):
        if self.state == PaymentState.QUEUE:
            payload = self.build_transfer_data()
            if DRY_RUN:
                print(json.dumps(payload, indent=True))
            else:
                try:
                    r = requests.post("http://localhost:{}/json_rpc".format(WALLET_PORT), data=json.dumps(payload))
                    r.raise_for_status()
                except requests.exceptions.HTTPError as e:
                    print("There was a problem talking to the RPC wallet - {}".format(e))
                response = r.json()
                if "result" in response.keys():
                    if "tx_hash" in response['result'].keys():
                        self.tx_hash = response['result']['tx_hash']
                    elif "tx_hash_list":
                        self.tx_hash = response['result']['tx_hash_list']
                if self.tx_hash:
                    self.state = PaymentState.PENDING
                    return True
                elif "error" in response.keys():
                    self.state = PaymentState.FAILED
                    self.fail_responses.append(response)
                    self.fail_count += 1
                    return False
                else:
                    self.state = PaymentState.FAILED
                    self.fail_count += 1
                    return False

    def get_payment_state(self):
        if self.tx_hash and self.state == PaymentState.PENDING:
            self._update_payment_state()
        return self.state

    def get_tx(self):
        if self.tx_hash and self.state == PaymentState.PENDING:
            if type(self.tx_hash) == list:
                resp = []
                for hash in self.tx_hash:
                    r = wallet_get_tx_id(hash, WALLET_PORT)
                    resp.append(r)
                return resp
            elif type(self.tx_hash) == str:
                return wallet_get_tx_id(self.tx_hash, WALLET_PORT)
        else:
            return None
    
    def write_tx_record(self):
        if self.state == PaymentState.PAIDONCHAIN or self.state == PaymentState.PENDING:
            tx = self.get_tx()
            with open("{}/{}.json".format(PAYOUT_DIR, self.tx_hash), mode='w') as fh:
                fh.write(json.dumps(tx, indent=True))
        elif self.state == PaymentState.FAILED or self.state == PaymentState.QUEUE:
            tx = self.get_tx()
            if not self.tx_hash:
                self.tx_hash = str(uuid4())
            with open("{}/{}-FAILED.json".format(PAYOUT_DIR, self.tx_hash), mode='w') as fh:
                if tx:
                    fh.write(json.dumps(tx, indent=True))
                else:
                    fh.write(json.dumps(self.build_transfer_data(), indent=True))
                if self.fail_responses:
                    fh.write(json.dumps(self.fail_responses, indent=True))

    def subtract_payouts(self):
        if self.state == PaymentState.PAIDONCHAIN:
            print("Payment is out on blockchain with tx_id {}".format(self.tx_hash))
            for pay in self.payments:
                unused_addr, cur_bal = wallet_db.get_wallet(pay.to_wallet)
                bal = cur_bal - pay.amount
                print("wallet {} old balance {} subtracting payout {} for total of {}".format(pay.to_wallet, cur_bal, pay.amount, bal))
                rc = wallet_db.set_wallet_value(pay.to_wallet, bal)
                print("db response on balance update is {}".format(rc))
            self.set_success()

    def set_success(self):
        self.state = PaymentState.SUCCESS

def topay_sort(a,b):
    if a['amount'] > b['amount']:
        return -1
    if a['amount'] == b['amount']:
        return 0
    if a['amount'] < b['amount']:
        return 1

def all_success(all_tx):
    response = PaymentState.SUCCESS
    for tx in all_tx:
        if tx.state != PaymentState.SUCCESS:
            return tx.state
    return response

if __name__ == "__main__":
    wallet_db = db()
    wallet_balances = wallet_db.get_wallets()
    to_pay = []
    for wallet in wallet_balances:
        if int(wallet['amount']) > THRESHOLD and wallet['address'] not in EXCLUDE_LIST:
            to_pay.append(wallet)
    print("Found {} wallets to pay\n".format(len(to_pay)))
    if len(to_pay) == 0:
        exit(0)
    new_pay = sorted(to_pay, key=functools.cmp_to_key(topay_sort))
    #print(json.dumps(new_pay, indent=True))
#    my_tx = Transaction()
#    for wall in to_pay:
#        my_pay = Payment(wall['address'], int(wall['amount']))
#        my_tx.add_payment(my_pay)

    wb = wallet_get_balance(WALLET_PORT)
    unspent = wb['result']['per_subaddress'][0]['num_unspent_outputs']

    all_txs = []
    for i in range(int(len(to_pay)/15)+1):
        tx = Transaction()
        first = True

        for x in range(15):
            if len(new_pay) == 0:
                break
            if first:
                first = False
                wall = new_pay.pop(0)
            else:
                wall = new_pay.pop()
            my_pay = Payment(wall['address'], int(wall['amount']))
            tx.add_payment(my_pay)
        all_txs.append(tx)
    print(f"Total tx's created {len(all_txs)}")

    while all_success(all_txs) != PaymentState.SUCCESS:
        for my_tx in all_txs:
            totalpay = 0
            for pay in my_tx.payments:
                totalpay += pay.amount
            wallet_balance = wallet_get_balance(WALLET_PORT)
            unlocked_balance = wallet_balance['result']['unlocked_balance']
            balance = wallet_balance['result']['balance']
            if balance <= totalpay:
                print("Wallet has less funds than needed for tx have - have {} need {}".format(balance, totalpay))
                continue
            if my_tx.state == PaymentState.QUEUE:
                if unlocked_balance <= totalpay:
                    print("Unlocked balance does not have enough to pay - waiting - have {} need {} - total bal {}".format(unlocked_balance, totalpay, balance))
                    wallet_balance = wallet_get_balance(WALLET_PORT)
                    unlocked_balance = wallet_balance['result']['unlocked_balance']
                else:
                    my_tx.send_tx_to_wallet_rpc()
            elif my_tx.state == PaymentState.PENDING:
                print("Payment is pending on blockchain with tx_id {}".format(my_tx.tx_hash))
                my_tx.get_payment_state()
            
            if my_tx.state == PaymentState.PAIDONCHAIN:
                my_tx.subtract_payouts()
                my_tx.write_tx_record()

            if my_tx.state == PaymentState.FAILED:
                print("Payment failed")
                if (my_tx.fail_count > 2 or my_tx.tx_hash):
                    my_tx.write_tx_record()
                elif my_tx.fail_count < 2 and my_tx.tx_hash == None:
                    print("Resetting to PaymentState.QUEUE")
                    my_tx.state = PaymentState.QUEUE

            if my_tx.state == PaymentState.SUCCESS:
                print(f"{my_tx.tx_hash} SUCCESSFUL")
            else:
                print("Tx is currently {} with {}".format(my_tx.state, my_tx.tx_hash))
        sleep(2)



