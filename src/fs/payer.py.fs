payout process functional spec

1. gather all wallets with pending balance over threshold
2. provide count of total wallets to payout
3. provide total to payout
4. validate wallet has enough to payout
5. create batchs of 15 to payout, and continue payout while there is enough unlocked balance
6. poll for balance unlock
7. retrigger pending remaining payouts and repeat 6/7 loop
8. custom thresholds finally lol
9. payout at specific daily or weekly slot.


payment - queue, pending, successful, failed

5/6 are currently sequential consider async
8. once we're out of prototyping stage
9. this is cron or just manual until we're sure it's 100%

