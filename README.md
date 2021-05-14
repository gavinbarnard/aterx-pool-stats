# aterx-pool-stats
A statistics collection and front end UI for https://github.com/jtgrassie/monero-pool

Simple install

git clone https://github.com/gavinbarnard/aterx-pool-stats

cp aterx-pool-stats/src/sample-pool-stats.conf ~/pool-stats.conf

make sure all config lines, and that all directories referenced exist
and are correct and that the file can be parsed with jq .

    {
        "pooldd": "/path/to/datadir",                       # path to the monero-pool data dir
        "v0_template_html": "/path/to/pool.template.html",  # path to template HTML file
        "sitename": "Monero Mining Pool",                   # name of your pool in front end UI
        "stats_dir": "/path/to/store/stats",                # path to store http://$site_up/stats every minute
        "site_ip": "x.y.a.b:port",                          # the http port of the monero-pool
        "script_dir": "/path/to/scripts",                   # the path to the src dir of this repo
        "pool_logo": "https://site.fqdn.com/logo.png",      # path to your logo
        "block_records": "/path/to/block_records",          # path to store block effort files, last stat file before pool blocks increased
        "monerod_rpc_port": 18081,                          # monerod's rpc port used for monerod/monero-pool block cross validation.
        "monero_wallet_rpc_port": 28084                     # monero-wallet-rpc server of the pool wallet to get outbound transfers
    }




create the neccesary locations with nginx to host your website files.
see sample.nginx.conf

For the SSI replacements by report.py see: see pool.template.html as an example

run the ./exporter.sh script and validate it works
Change the path in this script to the config file if not
in the home directory

setup a cronjob to run exporter.sh every minute

    * * * * * /path/to/aterx-pool-stats/src/exporter.sh

setup and run the uwsgi application with the uwsgi.ini, modify to run per your
own parameters.  You can launch the service in a screen session with the 
following command while in the src directory:

    uwsgi --ini uwsgi.ini