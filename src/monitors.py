from util.rpc import monerod_get_height, moneropool_get_stats

def main():
    ### get pool stats ###

    local_stats = moneropool_get_stats("localhost:4243")

    ### get external pools stats ###

    external_sites = ['xmrzone.net:443', 'monerop.com:80', 'xmrvsbeast.com:443' ]
    external_stats = {}
    for site in external_sites:
        ssl = False
        if site[-4:] == ":443":
            ssl = True
        external_stats[site] = moneropool_get_stats(site, None, ssl)

    ### get monerod stats ###

    local_monerod_height = monerod_get_height(18081)

    for site in external_stats.keys():
        if local_stats['network_height'] != external_stats[site]['network_height']:
            if local_stats['network_height'] < external_stats[site]['network_height']:
                print("Mismatch we're behind {}:{} and local:{}".format(
                    site, external_stats[site]['network_height'], local_stats['network_height']
                ))
            if local_stats['network_height'] > external_stats[site]['network_height']:
                print("mismatch but We're ahead of {}:{} and local:{}".format(
                    site, external_stats[site]['network_height'], local_stats['network_height']
                ))
        if local_stats['network_height'] != local_monerod_height - 1:
            print("Mismatch between pool height {} and monerod height {}".format(
                local_stats['network_height'], local_monerod_height
            ))

if __name__ == "__main__":
    main()