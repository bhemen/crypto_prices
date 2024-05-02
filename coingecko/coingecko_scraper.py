"""
    Scrape price data from coingecko's API
    Write errors to coingecko_errors.csv
"""

from pycoingecko import CoinGeckoAPI
from requests import HTTPError
import arrow
import time
import progressbar

cg = CoinGeckoAPI()

allcgcoins = cg.get_coins_list()
allids = [x['id'] for x in allcgcoins]

def get_prices(cg, coin_id, start_time, end_time):
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
start_date = end_date.shift(days=-3) #Coingecko only allows querying last 365 days with the free plan

error_filename = "coingecko_errors.csv"
files = {}

for c in ids_to_scrape:
    filename = c.replace("-", "_")
    filename += "_usd.csv"
    filename = f"../data/new_{filename}"
    files[c] = open(filename, "w")

num_days = (end_date-start_date).days
date_range = arrow.Arrow.span_range('day',start_date,end_date)

print( f"Grabbing price data for {ids_to_scrape}" )
print( f"{start_date.format('YYYY-MM-DD')} - {end_date.format('YYYY-MM-DD')} ({num_days} days)" )

day_num = 0
with progressbar.ProgressBar(max_value=num_days) as bar:
    for day_start, day_end in date_range:
        bar.update(day_num)
        #print( f"Grabbing data for {day_start.format('YYYY-MM-DD')}" )
        for c in ids_to_scrape:
            try:                
                prices = get_prices(cg, c, day_start.timestamp(), day_end.timestamp() )
                if prices["prices"]:
                    for price in prices["prices"]:
                        files[c].write(f"{price[0]},{price[1]}\n")
            except Exception as e:
                # simply log the coin and timestamp, not hard to regrab this data
                with open( error_filename, 'a') as error_file:
                    error_file.write(f"{c},{day_start.timestamp()},{e}\n")
        day_num += 1

for f in files:
    f.close()
