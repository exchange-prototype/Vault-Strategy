"use strict";
import numpy as np

Q96 = 1;

def mulDiv(a, b, multiplier):
  return (a * b) / multiplier;

def getLiquidityForAmount0(sqrtRatioAX96, sqrtRatioBX96, amount0):
  if (sqrtRatioAX96 > sqrtRatioBX96):
    [sqrtRatioAX96, sqrtRatioBX96] = [sqrtRatioBX96, sqrtRatioAX96];
  intermediate = mulDiv(sqrtRatioAX96, sqrtRatioBX96, Q96);
  return mulDiv(amount0, intermediate, sqrtRatioBX96 - sqrtRatioAX96);

def getLiquidityForAmount1(sqrtRatioAX96, sqrtRatioBX96, amount1):
  if (sqrtRatioAX96 > sqrtRatioBX96):
    [sqrtRatioAX96, sqrtRatioBX96] = [sqrtRatioBX96, sqrtRatioAX96];
  return mulDiv(amount1, Q96, sqrtRatioBX96 - sqrtRatioAX96);

def getLiquidityForAmounts(
  sqrtRatioX96,
  sqrtRatioAX96,
  sqrtRatioBX96,
  amount0,
  amount1
):
  liquidity = None;
  if (sqrtRatioAX96 > sqrtRatioBX96):
    [sqrtRatioAX96, sqrtRatioBX96] = [sqrtRatioBX96, sqrtRatioAX96];
  if (sqrtRatioX96 <= sqrtRatioAX96):
    liquidity = getLiquidityForAmount0(sqrtRatioAX96, sqrtRatioBX96, amount0);
  else:
    if (sqrtRatioX96 < sqrtRatioBX96):
      liquidity0 = getLiquidityForAmount0(
        sqrtRatioX96,
        sqrtRatioBX96,
        amount0
      );
      liquidity1 = getLiquidityForAmount1(
        sqrtRatioAX96,
        sqrtRatioX96,
        amount1
      );
      liquidity = liquidity0 if liquidity0 < liquidity1 else liquidity1;
    else:
      liquidity = getLiquidityForAmount1(sqrtRatioAX96, sqrtRatioBX96, amount1);

  return liquidity;

def getAmount0ForLiquidity(sqrtRatioAX96, sqrtRatioBX96, liquidity):
  if (sqrtRatioAX96 > sqrtRatioBX96):
    [sqrtRatioAX96, sqrtRatioBX96] = [sqrtRatioBX96, sqrtRatioAX96];
  return (
    mulDiv(liquidity, sqrtRatioBX96 - sqrtRatioAX96, sqrtRatioBX96) /
    sqrtRatioAX96
  );

def getAmount1ForLiquidity(sqrtRatioAX96, sqrtRatioBX96, liquidity):
  if (sqrtRatioAX96 > sqrtRatioBX96):
    [sqrtRatioAX96, sqrtRatioBX96] = [sqrtRatioBX96, sqrtRatioAX96];
  return mulDiv(liquidity, sqrtRatioBX96 - sqrtRatioAX96, Q96);

def getAmountsForLiquidity(
  sqrtRatioX96,
  sqrtRatioAX96,
  sqrtRatioBX96,
  liquidity
):
  amount0 = None;
  amount1 = None;
  if (sqrtRatioAX96 > sqrtRatioBX96):
    [sqrtRatioAX96, sqrtRatioBX96] = [sqrtRatioBX96, sqrtRatioAX96];
  if (sqrtRatioX96 <= sqrtRatioAX96):
    amount0 = getAmount0ForLiquidity(sqrtRatioAX96, sqrtRatioBX96, liquidity);
  elif (sqrtRatioX96 < sqrtRatioBX96):
    amount0 = getAmount0ForLiquidity(sqrtRatioX96, sqrtRatioBX96, liquidity);
    amount1 = getAmount1ForLiquidity(sqrtRatioAX96, sqrtRatioX96, liquidity);
  else:
    amount1 = getAmount1ForLiquidity(sqrtRatioAX96, sqrtRatioBX96, liquidity);
  return [amount0, amount1];

def getTokenAWeight(pxa, px, pxb):
    baseLiquidity = getLiquidityForAmounts(np.sqrt(px), 0, 1e16, 1, px);
    virtualLiquidityPreCalc = getLiquidityForAmounts(np.sqrt(px), np.sqrt(pxa), np.sqrt(pxb), 1, px);
    amountsOutBase = getAmountsForLiquidity(np.sqrt(px), 0, 1e16, baseLiquidity);
    amountsOutWLev = getAmountsForLiquidity(np.sqrt(px), np.sqrt(pxa), np.sqrt(pxb), virtualLiquidityPreCalc);
    return (px * amountsOutWLev[0])/(px * amountsOutWLev[0] + amountsOutWLev[1]);

def getEffFactor(pxa, px, pxb, tokenAWeight):
    virtualLiquidity = getLiquidityForAmounts(np.sqrt(px), np.sqrt(pxa), np.sqrt(pxb), 2 * tokenAWeight, 2 * (1 - tokenAWeight) * px);
    baseLiquidity = getLiquidityForAmounts(np.sqrt(px), 0, 1e16, 1, px);
    return virtualLiquidity/baseLiquidity;

def getActiveFrequency(pxa, pxb, df):
    return df.apply(lambda x: (x > pxa) & (x < pxb),axis=0).mean(axis=0).mean();

def getActiveCells(pxa, pxb, df):
    def process(x):
        return (x > pxa) & (x < pxb);
    return df.apply(process ,axis=0);

def calcIL(start, end, pxa, pxb, tokenAWeight):
    virtualLiquidityStart = getLiquidityForAmounts(np.sqrt(start), np.sqrt(pxa), np.sqrt(pxb), 2 * tokenAWeight, 2 * (1 - tokenAWeight) * start);
    baseLiquidityStart = getLiquidityForAmounts(np.sqrt(start), 0, 1e16, 1, start);
    liqPercDiff = abs(virtualLiquidityStart - baseLiquidityStart)/baseLiquidityStart;
    amountsEndwLev = getAmountsForLiquidity(np.sqrt(end), np.sqrt(pxa), np.sqrt(pxb), virtualLiquidityStart);
    if (amountsEndwLev[0] and amountsEndwLev[1]):
        valPool = amountsEndwLev[0] * end + amountsEndwLev[1];
    elif (amountsEndwLev[0]):
        valPool = amountsEndwLev[0] * end;
    else:
        valPool = amountsEndwLev[1];

    valHodl = 1 * end * tokenAWeight * 2 + 1 * start * (1-tokenAWeight) * 2;
    return (valPool-valHodl)/valHodl * 100;

def getILVector(df, pxa, pxb, tokenAWeight):
    results = df.apply(lambda x: calcIL(x.iloc[0], x.iloc[-1], pxa, pxb, tokenAWeight), axis=0);
    return results;

def getReturnsVector(pxa, pxb, df, eff, yr, tokenAWeight):
    return (getActiveCells(pxa,pxb,df) * eff * yr).sum(axis=0) + getILVector(df, pxa, pxb, tokenAWeight);

def getReturnsVector(pxa, pxb, df, eff, yr, tokenAWeight):
    return (getActiveCells(pxa, pxb, df) * eff * yr).sum(axis=0) + getILVector(df, pxa, pxb, tokenAWeight);
