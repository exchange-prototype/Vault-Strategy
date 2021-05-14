import time
import requests, pandas as pd
from datetime import datetime
url = "https://chainvault.io/node/api/market/pool/backtest/uniswap/"
period="120d"
frequency="1h"

pools=[{"tokenA" : "WETH", "tokenB": "USDT"},
       {"tokenA" : "WETH", "tokenB": "USDC"},
       {"tokenA" : "WETH", "tokenB": "MKR"},
       {"tokenA" : "WETH", "tokenB": "UNI"},
       {"tokenA" : "WETH", "tokenB": "COMP"},
       {"tokenA" : "WETH", "tokenB": "WBTC"},]
for pool in pools:
  print("Scraping pool=",pool)
  urlFull = url + pool["tokenA"] + "/" + pool["tokenB"] + "/" + period + "/" + frequency;
  x = requests.get(urlFull).json()['data'];
  X = pd.DataFrame(data=x, columns=["cumFees","cumIL","tokenAPrice","tokenBPrice","timestamp"])
  X["time"]=[datetime.utcfromtimestamp(int(ele)) for ele in X["timestamp"]];
  X["close"]=X["tokenAPrice"]/X["tokenBPrice"];
  outName = pool["tokenA"]+pool["tokenB"]+".csv";
  X["fees"] = X["cumFees"].diff()
  X["fees"] = [ele if ele > 0 else 0 for ele in X["fees"]]
  X["cumFees"] = X["fees"].cumsum() ### clean out bad ticks, i.e. where volume->0
  X[["time","tokenAPrice","tokenBPrice","close","cumFees","cumIL"]].to_csv(outName, index=False);
  time.sleep(60)
