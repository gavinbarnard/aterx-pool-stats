# aterx-pool-stats
A statistics collection service for https://github.com/jtgrassie/monero-pool

Simple install

git clone https://github.com/gavinbarnard/aterx-pool-stats

cp aterx-pool-stats/src/sample-pool-stats.conf ~/pool-stats.conf

make sure all config lines are correct and that the file can be parsed with jq .

create the neccesary locations with nginx to host your website files.
see pool.template.html as an example

run the ./exporter.sh script and validate it works
Change the path in this script to the config file if not
in the home directory

setup a cronjob to run exporter.sh every minute

    * * * * * /path/to/aterx-pool-stats/src/exporter.sh