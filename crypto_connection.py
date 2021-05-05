from pycoingecko import CoinGeckoAPI

#import json

def coin_info(coin):
    return_data = {}
    return_data["error"] = 0
    #eudata = []
    usdata = {}
    cg = CoinGeckoAPI()
    #eudata = cg.get_price(ids=coin, vs_currencies="eur", include_24hr_vol="true", include_24hr_change="true"))
    usdata = cg.get_price(ids=coin, vs_currencies="usd", include_24hr_vol="true", include_24hr_change="true")
    if len(usdata) == 0:
        return_data["error"] = -1
    else:
        return_data["priceusd"] = usdata[coin]["usd"]
        return_data["usd_24h_vol"] = round(usdata[coin]["usd_24h_vol"],3)
        return_data["usd_24h_change"] = round(usdata[coin]["usd_24h_change"],3)
        
    return return_data
