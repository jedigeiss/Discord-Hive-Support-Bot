import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.style as style
import matplotlib
from datetime import datetime
from pycoingecko import CoinGeckoAPI



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
        coin_graphic(coin)
        
    return return_data

def coin_graphic(coin):
    months = mdates.MonthLocator()
    months_fmt = mdates.DateFormatter("%M")
    days = mdates.DayLocator()

    date = []
    worth = []
    cg = CoinGeckoAPI()
    data = cg.get_coin_market_chart_by_id(id=coin, vs_currency='usd',days='3')
    for row in data["prices"]:
        #print(datetime.fromtimestamp(int(row[0])/1000),row[1])
        date.append(datetime.fromtimestamp(int(row[0])/1000))
        worth.append(row[1])


    matplotlib.rcParams['font.family'] = "serif"
    #style.use("seaborn-poster")
    #style.use("ggplot")
    style.use("fivethirtyeight")

    fig, ax = plt.subplots()
    plt.xlabel("Datum", labelpad=15, fontsize=16)
    plt.xticks(rotation=0)
    plt.ylabel("Wert in $", labelpad=15, fontsize=16)
    plt.title("Kursverlauf für: %s" % coin.title(),fontsize=18)
    ax.grid(axis='y', linestyle='dotted')

    ax.plot(date,worth)
    ax.xaxis.set_major_locator(days)
    #ax.xaxis.set_major_formatter(months_fmt)

    plt.tight_layout()
    #fig.autofmt_xdate()
    # save the graph in the standard location for the calling function
    plt.savefig("pricechart.png")
    plt.close()

