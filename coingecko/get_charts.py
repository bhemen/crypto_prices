from tqdm import tqdm
import requests

coins = [ { 'id': 325, 'name': 'USDT' }, { 'id': 6319, 'name': 'USDC' } ]

base_url = "https://www.coingecko.com/price_charts/export/"

for c in coins:
    print( f"Getting {c['name']}" )
    url = base_url + str(c['id']) + "/usd.csv" 
    response = requests.get(url, stream=True)

    with open(c['name'] + "_history.csv", "wb") as handle:
        for data in tqdm(response.iter_content()):
            handle.write(data)
