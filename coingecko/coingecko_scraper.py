"""
    Scrape price data from coingecko's API
    Write errors to coingecko_errors.csv
"""

from pycoingecko import CoinGeckoAPI
from requests import HTTPError
import arrow
import time
import progressbar
import pandas as pd

cg = CoinGeckoAPI()

allcgcoins = cg.get_coins_list()
allids = [x['id'] for x in allcgcoins]

def get_market_data(cg, coin_id, start_time, end_time):
    """
        cg - coingecko object
        coin_id- coin id
        start_time - timestamp of start time
        end_time - timestamp of end time
        
    """
    # try 5 times max
    for _ in range(5):
        try:
            prices = cg.get_coin_market_chart_range_by_id(coin_id, "usd", start_time, end_time) #Get prices from coingecko (denominated in usd)
            return prices
        except HTTPError as e:
            # sleep 5 seconds if we get rate limited
            if e.response.status_code == 429:
                time.sleep(5)
    raise Exception("retried too many times after rate limited")

ids_to_scrape = [
    "1inch",
    "axie-infinity",
    "chainlink",
    "dai",
    "sai",
    "ethereum",
    "fei-usd",
    "frax",
    "shiba-inu",
    "tether",
    "liquity-usd",
    "unicorn-token",
    "uniswap",
    "usd-coin",
	"tribe-token",
	"wise-token11",
    "wrapped-bitcoin",
]

if len( set(ids_to_scrape).difference(allids) ) > 0:
	print( f"Error invalid id" )
	print( set(ids_to_scrape).difference(allids) )
	ids_to_scrape = list( set(ids_to_scrape).intersection(allids) )

end_date = arrow.utcnow()
start_date = end_date.shift(days=-364) #Coingecko only allows querying last 365 days with the free plan

error_filename = "coingecko_errors.csv"
files = {}

for c in ids_to_scrape:
    filename = c.replace("-", "_")
    filename += ".csv"
    filename = f"../data/cg_{filename}"
    files[c] = open(filename, "w")

num_days = (end_date-start_date).days
date_range = arrow.Arrow.span_range('day',start_date,end_date)

print( f"Grabbing price data for {ids_to_scrape}" )
print( f"{start_date.format('YYYY-MM-DD')} - {end_date.format('YYYY-MM-DD')} ({num_days} days)" )

day_num = 0
rows = {}
with progressbar.ProgressBar(max_value=num_days*len(ids_to_scrape)) as bar:
    for c in ids_to_scrape:
        rows[c] = []
        for day_start, day_end in date_range:
            bar.update(day_num)
            try:                
                md = get_market_data(cg, c, day_start.timestamp(), day_end.timestamp() )
                dates = [ p[0] for p in md['prices'] ]
                prices = [ p[1] for p in md['prices'] ]
                market_caps = [ mc[1] for mc in md['market_caps'] ]
                volumes = [ v[1] for v in md['total_volumes'] ]
                mc_dates = [ mc[0] for mc in md['market_caps'] ]
                v_dates = [ v[0] for v in md['total_volumes'] ]
                assert len(prices) == len(market_caps)
                assert len(market_caps) == len(volumes)
                assert all( dates[i] == mc_dates[i] for i in range(len(dates)) )
                assert all( dates[i] == v_dates[i] for i in range(len(dates)) )
                new_rows = [ { 'coin': c, 'ts': date, 'price': price, 'volume': volume, 'market_cap': market_cap } for date,price,volume,market_cap in zip(dates,prices,volumes,market_caps) ]
                rows[c] = rows[c] + new_rows
            except Exception as e: # When there is an error, log the coin and timestamp, then we can regrab the data later
                with open( error_filename, 'a') as error_file:
                    error_file.write(f"{c},{day_start.timestamp()},{e}\n")
            day_num += 1
        df = pd.DataFrame( rows[c] )
        if 'ts' in df.columns: #Convert Unix timestamp to datetime column
            try:
                df['date'] = pd.to_datetime( df['ts'], unit='ms' )
            except Exception as e:
                print( "Error converting dates" )
                print( e )
        print( f"Got {len(df)} observations for {c}" )
        df.to_csv(files[c], index=False)

