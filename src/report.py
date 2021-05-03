import json, datetime
from util.config import parse_config, cli_options

def convert_hz(hertz):
    hz = 0
    if hertz > 1000*1000*1000:
        hz = round(hertz / 1000*1000*1000, 2)
        r = "GH"
    elif hertz > 1000*1000:
        hz = round(hertz / 1000*1000, 2)
        r = "MH"
    elif hertz > 1000:
        hz = round(hertz / 1000, 2)
        r = "KH"
    elif hertz >= 0:
        hz = hertz
        r = "H"
    return "{}{}/s".format(hz,r)


def main():
    config_file = cli_options()
    config_items = parse_config(config_file)
    payout_fh = open(config_items['payout_file'])
    payout = json.loads(payout_fh.read())
    payout_fh.close()
    amounts = []
    counts = []
    dates = []
    for p in payout:
    # /1000000000000
        amount = p['amount']/1000000000000
        count = len(p['destinations'])
        date = datetime.datetime.fromtimestamp(p['timestamp'])
        amounts.append(amount)
        counts.append(count)
        dates.append(date)
    payout_insert = ""
    for i in range(0,len(amounts)):
        payout_insert += "{} XMR to {} Miners at {}<br/>".format(amounts[i], counts[i], dates[i])

    block_find_fh = open(config_items['block_find_out'])
    block_find = block_find_fh.read()
    block_find_fh.close()
    blocks_fh = open(config_items['block_inout'])
    blocks = blocks_fh.read()
    blocks_fh.close()
    template_fh = open(config_items['template_html'])
    template = template_fh.read()
    multi_fh = open(config_items['multi_out'])
    multi = multi_fh.read()
    multi_fh.close()
    average_fh = open(config_items['average_out'])
    pool_avg = int(average_fh.read())
    average_fh.close()
    pool_avg = convert_hz(pool_avg)
    if len(blocks.strip()) == 0:
        blocks = "None yet :("
    template_fh.close()
#    template = template.replace("<!-- BLOCKFIND --!>", block_find)
# temporary disable unsure I have the correct calculations in stats.py
    template = template.replace("<!-- PAYOUTLIST --!>", payout_insert)
    template = template.replace("<!-- SITENAME --!>", config_items['sitename'])
    template = template.replace("<!-- POOLLOGO --!>", config_items['pool_logo'])
    blocks = blocks.split("\n")
    del(blocks[len(blocks)-1])
    blocks.reverse()
    blocks = "<br>".join(blocks)
    template = template.replace("<!-- BLOCKLIST --!>", blocks)
    pool_hash = "Network HR vs Pool HR scale is roughly 1/{}".format(multi)
    template = template.replace("<!-- MULTI --!>", pool_hash)
    template = template.replace("<!-- AVERAGE --!>", pool_avg)
    pool_fh = open(config_items['pool_html'],'w')
    pool_fh.write(template)
    pool_fh.close()


if __name__ == "__main__":
    main()
