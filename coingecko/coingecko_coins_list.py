from pycoingecko import CoinGeckoAPI
import pandas as pd

cg = CoinGeckoAPI()

allcgcoins = cg.get_coins_list()

df = pd.DataFrame( allcgcoins )

df.to_csv( "coin_list.csv", index=False )

