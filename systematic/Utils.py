import math, LPMath, numpy as np, pandas as pd, scipy.stats as st
from datetime import datetime
from numpy.random import normal

def monteCarloSimulation(So, mu, vol, T, ns):
    """ A Monte Carlo simulator for GBM """
    #--------------------------------------------------- GEOMETRIC BROWNIAN MOTION ------------------------------------------------
    # Parameter Definitions

    # So    :   initial crypto price
    # mu    :   drift
    # dt    :   time increment (can be fraction of a timestep, we default to one step below)
    # T     :   length of the prediction time horizon(how many time points to predict, same unit with dt(days))
    # N     :   number of time points in prediction the time horizon -> T/dt
    # t     :   array for time points in the prediction time horizon [1, 2, 3, .. , N]
    # vol   :   standard deviation of step-length returns
    # ns    :   number of simulations
    # b     :   array for brownian increments
    # W     :   array for brownian path

    dt = 1;
    # Parameter Assignments
    N = T / dt;
    t = np.arange(1, int(N) + 1);
    sigma = vol*np.sqrt(dt);

    b = {str(scen): np.random.normal(0, 1, int(N)) for scen in range(1, ns + 1)};
    W = {str(scen): b[str(scen)].cumsum() for scen in range(1, ns + 1)};

    # Calculating drift and diffusion components
    drift = (mu - 0.5 * sigma**2) * t;
    diffusion = {str(scen): sigma * W[str(scen)] for scen in range(1, ns + 1)};
    # Making the predictions
    S = np.array([So * np.exp(drift + diffusion[str(scen)]) for scen in range(1, ns + 1)]);
    S = np.hstack((np.array([[So] for scen in range(ns)]), S)).T; # add So to the beginning series
    return S;

def getUpperBound(values, pct):
    """ Calculate value corresponding to percentile pct """

    return np.percentile(values, 100*pct)

def getBands(close, drift, diffusion, rebalWindow, nSimulations, liqOuterBand, rebalForward):
    """ Get bands for liquidity range and rebalance """

    '''
    ### We tested a MC approach, but chose to go w/ simpler std dev approach
    terminalValues = monteCarloSimulation(close, drift, diffusion, rebalWindow, nSimulations)
    outerRight = getUpperBound(terminalValues, liqOuterBand)
    outerLeft = close**2/outerRight #[outerLeft,outerRight] is geometrically symmetric about close
    stopRight = getUpperBound(terminalValues, rebalForward)
    stopLeft = close**2/stopRight #[stopLeft,stopRight] is geometrically symmetric about close
    '''

    outerRight = close*(1+st.norm.ppf(liqOuterBand)*diffusion*np.sqrt(rebalWindow));
    outerLeft = close**2/outerRight;  #[outerLeft,outerRight] is geometrically symmetric about close
    stopRight = close*(1+st.norm.ppf(rebalForward)*diffusion*np.sqrt(rebalWindow));
    stopLeft = close**2/stopRight; #[stopLeft,stopRight] is geometrically symmetric about close

    return [outerLeft, stopLeft, stopRight, outerRight];

def dtToMs(dt):
    """ datetime to miliseconds """

    epoch = datetime.utcfromtimestamp(0);
    delta = dt - epoch;
    return int(delta.total_seconds() * 1000);

def dtFromMs(ms):
    """ miliseconds to datetime """

    return datetime.utcfromtimestamp(ms / 1000.0);

def appendPosition(df, columns, data):
    """ add position to df """

    for i in range(len(columns)):
        df[columns[i]].append(data[i]);
    return df;

def calculatePnL(positions):
    positions['fees'] = positions['cumFees'].diff(); # diff cumulative fees to make a stream of fees
    pxa = positions['low'].iloc[0]; # Lower bound
    pxi = positions['tokenPriceA'].iloc[0]/positions['tokenPriceB'].iloc[0]; #starting price
    pxb = positions['high'].iloc[0]; # Upper bound
    effFactor = LPMath.getEffFactor(pxa, pxi, pxb, .5); # Capital efficiency multiplier
    totalIL, fees = 0, 0;
    results = [[0,0]];
    for i in range(1,len(positions)):
        pxf = positions['tokenPriceA'].iloc[i]/positions['tokenPriceB'].iloc[i]; # calculate new price
        iL = LPMath.calcIL(pxi, pxf, pxa, pxb, .5) + totalIL; # calculate IL at each step for given position and sum w/ rolling IL
        fees += 100 * effFactor * positions['fees'].iloc[i]; # multiply by 100 to make percent return

        if positions['note'].iloc[i] == 'new':
            pxa = positions['low'].iloc[i];
            pxi = positions['tokenPriceA'].iloc[i]/positions['tokenPriceB'].iloc[i];
            pxb = positions['high'].iloc[i];
            effFactor = LPMath.getEffFactor(pxa, pxi, pxb, .5);
            totalIL = iL;
        results.append([iL, fees]);
    return pd.DataFrame(data=results, columns=["iL", "fees"]);
