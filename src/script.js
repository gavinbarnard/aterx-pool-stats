// format numbers
const formatHashes = (h) => {
    if (h < 1e-12) return "0 H";
    if (h < 1e-9) return max_precision(h*1e+12, 0) + " pH";
    if (h < 1e-6) return max_precision(h*1e+9, 0) + " nH";
    if (h < 1e-3) return max_precision(h*1e+6, 0) + " μH";
    if (h < 1) return max_precision(h*1e+3, 0) + " mH";
    if (h < 1e+3) return parseInt(h) + " H";
    if (h < 1e+6) return max_precision(h*1e-3, 2) + " KH";
    if (h < 1e+9) return max_precision(h*1e-6, 2) + " MH";
    return max_precision(h*1e-9, 2) + " GH";
}			
const format_last_time = last => {
    const diff = (new Date().getTime() / 1000) - Number(last);
    if (last == 0) return "None yet";
    if (diff <= 0) return "Just now";
    if (diff < 60) return `${diff} second${(diff != 1 ? "s" : "")} ago`;
    // NOTE: reduce parseInt
    if (diff < 3600) return parseInt(diff/60) + " minute" + (parseInt(diff/60) != 1 ? "s" : "") + " ago";
    if (diff < 86400) return parseInt(diff/3600) + " hour" + (parseInt(diff/3600) != 1 ? "s" : "") + " ago";
    return parseInt(diff/86400) + " day" + (parseInt(diff/86400) != 1 ? "s" : "") + " ago";
}
const max_precision = (n, p) => {
    return Number(parseFloat(n).toFixed(p));
}
const format_round_hashrate = (round_hashes, last_block_found) => {
    if (last_block_found == 0) return 0;
    const diff = (new Date().getTime() / 1000) - last_block_found;
    if (diff <= 0) return 0;
    return `${formatHashes(round_hashes / diff)}/s`;
}

// make update functions
async function getFromAPI(route) {
    const rawFetch = await fetch(`https://pool.aterx.com/${route}`);
    if (!rawFetch.ok) return;
    return await rawFetch.json();
}
const bonusUpdate = async() => {
    const APIData = await getFromAPI("0/bonus_address");
    let bonus_html = document.getElementById("bonus_rig");
    bonus_html.innerHTML = `BonusRig target: ${APIData.substring(1,7)}`;
}
const multiUpdate = async() => {
    const APIData = await getFromAPI("0/multi");
    let multi_ele = document.getElementById("multi");
    multi_ele.innerHTML = `Pool HR to Network HR is about 1:${APIData.multi}`
}
const rigUpdate = async() => {
    const APIData = await getFromAPI("workers");
    let connected_rigs = document.getElementById("rig_list");
    connected_rigs.innerHTML = "";
    for(i = 0; i < APIData.length; i++) {
        connected_rigs.innerHTML+=`${connected_rigs.innerHTML} ${isNaN(APIData[i]) ? APIData[i].replace("<", "&lt;").replace(">", "&gt;") : formatHashes(APIData[i])} :&nbsp; ${APIData[i+1]} </br>`;
    }
}
const paymentsUpdate = async(type) => {
    const APIData = await getFromAPI(`0/payments${type == "type" ? "": ".summary"}`);
    updatePayments(APIData);
}
const graphUpdate = async() => {
    const APIData = getFromAPI("0/graph_stats.json")
    updateGraph(APIData);
} 

const statsUpdate = async () => {
    // NOTE work on this
    const APIData = await getFromAPI("stats")
    const rhr = document.getElementById("round_hashrate");
    rhr.innerHTML = format_round_hashrate(APIData.round_hashes, APIData.last_block_found);
    const miner_balance = document.getElementById("miner_balance");
    miner_balance.innerHTML = APIData.miner_balance;
    const worker_count = document.getElementById("worker_count");
    worker_count.innerHTML = APIData.worker_count;
    const pool_fee = document.getElementById("pool_fee");
    pool_fee.innerHTML = `${APIData.pool_fee*100}%`;
    const pool_port = document.getElementById("pool_ssl_port");
    pool_port.innerHTML = APIData.pool_port;
    const allow_self_select = document.getElementById("allow_self_select");
    allow_self_select.innerHTML = APIData.allow_self_select ? "Yes" : "No";
    const payment_threshold = document.getElementById("payment_threshold");
    payment_threshold.innerHTML = APIData.payment_threshold;
    const connected_miners = document.getElementById("connected_miners");
    connected_miners.innerHTML = APIData.connected_miners;
    const round_hashes = document.getElementById("round_hashes");
    round_hashes.innerHTML = `${max_precision(APIData.round_hashes*100 / APIData.network_difficulty, 1)}% (${formatHashes(APIData.round_hashes)} / ${formatHashes(APIData.network_difficulty)})`;
    const last_template_fetched = document.getElementById("last_template_fetched");
    last_template_fetched.innerHTML = format_last_time(APIData.last_template_fetched);
    const last_block_found = document.getElementById("last_block_found");
    last_block_found.innerHTML = format_last_time(APIData.last_block_found);
    const pool_blocks_found = document.getElementById("pool_blocks_found");
    pool_blocks_found.innerHTML = APIData.pool_blocks_found;
    const network_height = document.getElementById("network_height");
    network_height.innerHTML = APIData.network_height;
    const network_hashrate = document.getElementById("network_hashrate");
    network_hashrate.innerHTML = `${formatHashes(APIData.network_hashrate)}/s`;
    const pool_hashrate = document.getElementById("pool_hashrate");
    pool_hashrate.innerHTML = `${formatHashes(APIData.pool_hashrate)}/s`;
}

// update funtions
function updatePayments(payment_data){
    // NOTE: work on this
    ptype = document.getElementById("payout_type");
    payments_t = document.getElementById("payments_table");
    payments_t.innerHTML = "";
    for (i = 0; i < payment_data.length; i++){
        payments_t.innerHTML += `<tr><td>${(payment_data[i][ptype.innerHTML == "pool" ? 'reward' : "amount"] / 1e+12)} XMR to ${payment_data[i][ptype.innerHTML == "pool" ? 'miner_count' : 'address']} ${ptype.innerHTML == "pool"?'miners':""} on ${new Date(payment_data[i][ptype.innerHTML == "pool" ? 'timestamp' : 'dt']*1000).toGMTString()}</td></tr>`
    }
}
function updateBlocks(block_data){
    // NOTE: work on this
    let now = new Date();
    const thirty_days_ago = new Date(now.setDate(now.getDate() - 30));
    let found_within_thirty = 0;
    block_t = document.getElementById("block_table");
    block_t.innerHTML = "<tr><td>Height</td><td>Status</td><td>Hash Match</td><td>To Unlock</td><td>Date</td><td>Reward</td><td>Effort</td></tr>";
    let maxeff = 0;
    uncounted_blocks = 0;
    for (i = 0; i < block_data.length; i++){
        if (block_data[i].status != "ORPHANED") {
            maxeff = maxeff + block_data[i].effort;
        } else {
            uncounted_blocks = uncounted_blocks + 1;
        }
        d = new Date(block_data[i].timestamp*1000);
        if (block_data[i].timestamp*1000 >= thirty_days_ago){
            found_within_thirty = found_within_thirty + 1;
        }
        block_t.innerHTML = block_t.innerHTML + "<tr><td>" + block_data[i].height + "</td><td>" + block_data[i].status + "</td><td>" + block_data[i].hash_match + "</td><td> " + block_data[i].blocks_to_unlock + "/60</td><td>" + d.toGMTString() + "</td><td>" + block_data[i].reward/1000000000000 + "</td><td>" + block_data[i].effort + "%</td></tr>";
    }
    avgeff = maxeff/(block_data.length-uncounted_blocks);
    block_t.innerHTML = block_t.innerHTML + "<tr><td></td><td></td><td></td><td></td><td></td><td>Average Effort</td><td>"+avgeff.toFixed(2)+"%</td></tr>"
    block_count = document.getElementById("block_count");
    block_count.innerHTML = "We have found " + found_within_thirty + " blocks in the last 30 days";
}
async function updateGraph(){
    const graph_data = await getFromAPI('0/graph_stats.json')
    const graphAPIData = await getFromAPI('0/pplns_est')
    const dark_mode = JSON.parse(getCookie("dark_mode") ?? false);
   
    let ctx = document.getElementById("shittygraph").getContext('2d');
    ctx.fillStyle = dark_mode ? "black" : "white"
    ctx.fillRect(0, 0, 900,150);

    let phr = 0;
    for (n = 0; n < graph_data.length; n++) {
        phr = phr + graph_data[n].pr
        if ( (n+1)%10 == 0 ){
            ctx.fillStyle = dark_mode ? "#080808" : "#F8F8F8";
            ctx.fillRect(n,0,1,150);
        }
        ctx.fillStyle = "#FFA500";
        ctx.fillRect(n,graph_data[n].pavg,1,1);
        ctx.fillStyle = "#00FF00";
        ctx.fillRect(n,graph_data[n].prp,1,1);
        ctx.fillStyle = "#FF0000";
        ctx.fillRect(n,graph_data[n].nrp,1,1);
        if (graph_data[n]['ts'] > graphAPIData.pplns_end){
            ctx.fillStyle = "#009696";
            ctx.fillRect(n, 148, 1,1);
        }
    }
    pavg = (phr/900).toFixed(2);
    document.getElementById("poolavg").innerHTML = `${formatHashes(pavg)}/s`;

    blockfind = document.getElementById("blockfind");
    b_chance = pavg / graph_data[graph_data.length-1].nr * 30 * 24 * 30
    if (b_chance>2){
        b_chance--;
    }
    blockfind.innerHTML = `At the pool average hashrate we will hopefully find about ${b_chance.toFixed(2)} blocks every 30 days</br>`;
    if (graphAPIData.pplns_end != 0){
        d = new Date(graphAPIData.pplns_end*1000);
        pplns_block = document.getElementById("pplns_block");
        pplns_block.innerHTML = "<font color='#009696'>The PPLNS Window goes back until roughly " + d.toGMTString() + "</font></br>";
    }
}

// toggle functions
function togglePayout(){
    let ptype = document.getElementById("payout_type");
    const ptypeToggle = ptype.innerHTML == "pool" ? "personal" : "pool"
    ptype.innerHTML = ptypeToggle;
    paymentsUpdate(ptypeToggle)
}
const toggleDark = toggle => {
    let dark_mode = JSON.parse(getCookie("dark_mode") ?? false)

    if (toggle) dark_mode = !dark_mode

    const address_div = document.getElementById("address");
    address_div.style.borderBottom = dark_mode ? "1px dashed white" : "1px dashed black"
    document.body.style.background = dark_mode ? "#000000" : "#FFFFFF";
    document.body.style.color = dark_mode ? "#FFFFFF" : "#000000";
    
    const x = document.querySelectorAll("a");
    for (i = 0; i < x.length; i++) x[i].className = dark_mode ? "adark" : "alight";

    setCookie("dark_mode", dark_mode);
}

// stats funtions
function hidepoolstats(){
    document.getElementById("graph_nr").innerHTML = "";
    document.getElementById("graph_pr").innerHTML = "";
    poolstate = document.getElementById("poolstate").style.opacity = 0.0;
    gts.innerHTML = "";
}
async function poolstats(e){
    // NOTE: work on this
    let poolstate = document.getElementById("poolstate");
    poolstate.style.position = "fixed";
    poolstate.style.top = (e.pageY-75) - window.scrollY +"px";
    poolstate.style.left = e.pageX + "px";
    poolstate.style.opacity = 100;

    const stat_lookup = e.clientX - e.target.getBoundingClientRect().left;

    const graph_data = await getFromAPI('0/graph_stats.json')
    document.getElementById("graph_nr").innerHTML = `${formatHashes(graph_data[stat_lookup].nr)}/s`
    document.getElementById("graph_pr").innerHTML = `${formatHashes(graph_data[stat_lookup].pr)}/s`
    document.getElementById("graph_dt").innerHTML = new Date(graph_data[stat_lookup].ts*1000).toLocaleString();
}

// get and set cookies
const getCookie = cname => {
    let ca = decodeURIComponent(document.cookie).split('; '), json = {};
    for (let i = 0; i < ca.length; i++) {
        json[ca[i].split("=")[0]]=ca[i].split("=")[1]
    }
    return json[cname];
}
const setCookie = (key, value) => {
    let expires = new Date();
    expires.setTime(expires.getTime() + (1 * 24 * 60 * 60 * 1000));
    document.cookie = key + '=' + value + ';expires=' + expires.toUTCString();
}

// html functions
window.onload = () => {
    document.getElementById("address").addEventListener("blur", e=>{
        setCookie("wa", this.innerText)
        window.location.reload();
    });

    const walletAddress = getCookie("wa")
    if (walletAddress && /^[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]+$/.test(walletAddress)){
        const m = document.querySelectorAll(".miner");
        for (let i=0; i<m.length; i++){
            m[i].style = "display: table-row;";
        }
        document.getElementById("address").innerText = walletAddress;
    }
    
    const get_stats = async () => {
        multiUpdate()
        updateBlocks(await getFromAPI("0/blocks.all"));
        paymentsUpdate(document.getElementById("payout_type").innerHTML)
        statsUpdate()
        bonusUpdate()
        rigUpdate()
        graphUpdate()
        paymentsUpdate("pool")
    }
    setInterval(get_stats, 30000);
    get_stats();
    toggleDark()
};