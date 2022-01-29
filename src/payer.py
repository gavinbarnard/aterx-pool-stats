# payer routine for pool.aterx.com

import json
from uuid import uuid4
import requests
from enum import Enum
from time import sleep
from util.moneropooldb import db 
from util.rpc import wallet_get_tx_id, wallet_get_balance

THRESHOLD = int(0.005 * 1e12)
WALLET_PORT = 28094
DATA_DIR = "/tmp/testbuild/data-dir"
PAYOUT_DIR = "/home/monero/payout_dir"

class PaymentState(Enum):
    QUEUE = 0
    PENDING = 1
    SUCCESS = 2
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
        self.fail_count = 0
        self.fail_responses = []

class Transaction(object):
    def __init__(self, state=PaymentState.QUEUE):
        self.payments = []
        self.amount = 0
        self.state = state
        self.tx_hash = None

    def _update_payment_state(self):
        if self.tx_hash and self.state == PaymentState.PENDING:
            tx = self.get_tx()
            if "result" in tx.keys():
                if "transfer" in tx['result'].keys():
                    if "type" in tx['result']['transfer'].keys():
                        if tx['result']['transfer']['type'] == "out":
                            self.state = PaymentState.SUCCESS
                        elif tx['result']['transfer']['type'] == "failed":
                            self.state = PaymentState.FAILED
                        elif tx['result']['transfer']['type'] == "pending":
                            self.state = PaymentState.PENDING

    def add_payment(self, payment: Payment):
        if len(self.payments) >= 15:
            raise TransactionFull
        if payment not in self.payments:
            self.payments.append(payment)
        else:
            raise PaymentAlreadyInTransaction

    def build_transfer_data(self):
        data = {
            "jsonrpc": "2.0",
            "id": "0",
            "method": "transfer",
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
            try:
                r = requests.post("http://localhost:{}/json_rpc".format(WALLET_PORT), data=json.dumps(payload))
                r.raise_for_status()
            except requests.exceptions.HTTPError as e:
                print("There was a problem talking to the RPC wallet - {}".format(e))
            response = r.json()
            if "result" in response.keys():
                if "tx_hash" in response['result'].keys():
                    self.tx_hash = response['result']['tx_hash']
                    self.state = PaymentState.PENDING
            if self.tx_hash:
                return True
            else:
                self.state = PaymentState.FAILED
                return False

    def get_payment_state(self):
        if self.tx_hash and self.state == PaymentState.PENDING:
            self._update_payment_state()
        return self.state

    def get_tx(self):
        if self.tx_hash and self.state == PaymentState.PENDING:
            return wallet_get_tx_id(self.tx_hash, WALLET_PORT)
        else:
            return None
    
    def write_tx_record(self):
        if self.state == PaymentState.SUCCESS or self.state == PaymentState.PENDING:
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

if __name__ == "__main__":
    wallet_db = db()
    wallet_balances = wallet_db.get_wallets()
    to_pay = []
    for wallet in wallet_balances:
        if int(wallet['amount']) > THRESHOLD:
            to_pay.append(wallet)
    txs_needed = int(len(to_pay)/15)
    if txs_needed % 15 != 0:
        txs_needed += 1
    print("Found {} wallets to pay\nNeed {} txes\n".format(len(to_pay), txs_needed))
    outbound_tx = []
    for i in range(0, txs_needed):
        my_tx = Transaction()
        for n in range(0, 15):
            idx = i*15+n
            if idx >= len(to_pay):
                break
            my_pay = Payment(to_pay[idx]['address'], int(to_pay[idx]['amount']))
            try:
                my_tx.add_payment(my_pay)
            except TransactionFull or PaymentAlreadyInTransaction as e:
                print("Error {} for {}".format(e,to_pay[idx]['address']))
        outbound_tx.append(my_tx)
    print("Created {} txes".format(len(outbound_tx)))

    for tx in outbound_tx:
        totalpay = 0
        for pay in tx.payments:
            totalpay += pay.amount
        wallet_balance = wallet_get_balance(WALLET_PORT)
        unlocked_balance = wallet_balance['result']['unlocked_balance']
        balance = wallet_balance['result']['balance']
        if balance <= totalpay:
            print("Wallet has less funds than needed for tx have - have {} need {}".format(balance, totalpay))
            exit(1)

        while unlocked_balance <= totalpay:
            print("Unlocked balance does not have enough to pay - waiting - have {} need {} - total bal {}".format(unlocked_balance, totalpay, balance))
            wallet_balance = wallet_get_balance(WALLET_PORT)
            unlocked_balance = wallet_balance['result']['unlocked_balance']
            sleep(10)
        
        while tx.state == PaymentState.QUEUE or tx.state == PaymentState.PENDING:
            if tx.state == PaymentState.QUEUE:
                tx.send_tx_to_wallet_rpc()
            elif tx.state == PaymentState.PENDING:
                while tx.state == PaymentState.PENDING:
                    print("Payment is pending on blockchain with tx_id {}".format(tx.tx_hash))
                    tx.get_payment_state()
                    sleep(10)
        
        tx.write_tx_record()
        if tx.state == PaymentState.SUCCESS:
            print("Payment is out on blockchain with tx_id {}".format(tx.tx_hash))
            for pay in tx.payments:
                unused_addr, cur_bal = wallet_db.get_wallet(pay.to_wallet)
                bal = cur_bal - pay.amount
                print("wallet {} old balance {} subtracting payout {} for total of {}".format(pay.to_wallet, cur_bal, pay.amount, bal))
                rc = wallet_db.set_wallet_value(pay.to_wallet, bal)
                print("db response on balance update is {}".format(rc))
        else:
            print("Transaction failed")


