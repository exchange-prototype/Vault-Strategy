from Algo import Algo
from datetime import datetime
import configparser, logging, sys, numpy as np, pandas as pd, scipy.stats as st, Utils

class UniswapV3LP(Algo):

    def __init__(self):
        """ Initialize """

        super().__init__();
        self.logger = logging.getLogger("UniswapV3LP");
        self.logger.info("Initialized UniswapV3LP");

        return

    def parseConfig(self, config):
        """ Parse Input Config """

        self.logger.info("Parsing input");
        super().parseConfig(config);
        self.rollingWindow = config["rollingWindow"]
        self.rebalWindow = config["rebalWindow"]
        self.nSimulations = config["nSimulations"]
        self.liqOuterBand = config["liqOuterBand"]
        self.rebalForward = config["rebalForward"]
        self.useDrift = config["useDrift"]
        self.verbose = config["verbose"]

        return

    def getData(self):
        """ Collect Data -- According to specified symbols and fields """

        self.logger.info("Getting data");
        super().getData();

        return

    def generateSignal(self):
        """ Generate Signal for input to Portfolio Construction """

        self.logger.info("Generating signal");
        self.data['returns'] = self.data['close'].pct_change(1);
        self.data['rollingMean'] = self.data['returns'].rolling(self.rollingWindow).mean();
        self.data['rollingStd'] = self.data['returns'].rolling(self.rollingWindow).std();
        self.data = self.data[(self.data.index >= self.sdt) & (self.data.index < self.edt)];

        return

    def generatePositions(self):
        """ Generate Signal for input to Portfolio Construction """

        self.logger.info("Generating positions");
        # Downsample data according to config param

        positions = {'time':[],'type':[],'fracSize':[], 'low':[],'high':[], 'note':[],'tokenAPrice':[],'tokenBPrice':[], 'cumFees':[]}
        end_date = self.data.index[self.rollingWindow]
        outerLeft, outerRight = np.nan, np.nan
        stopLeft, stopRight = np.nan, np.nan
        for i in range(self.data.shape[0]):
            if (i < self.rollingWindow): continue
            date = self.data.index[i]
            fees = self.data.iloc[i]['cumFees']
            close = self.data.iloc[i]['close']
            drift = self.data.iloc[i]['rollingMean'] if self.useDrift else 0
            diffusion = self.data.iloc[i]['rollingStd']
            tokenAPrice, tokenBPrice = self.data.iloc[i]['tokenAPrice'], self.data.iloc[i]['tokenBPrice']
            if date < end_date:
                # check if stopping out
                if ((close > stopRight) or (close < stopLeft)):
                    # calculate fees during interval
                    outerLeft, stopLeft, stopRight, outerRight = Utils.getBands(close, drift, diffusion, self.rebalWindow, self.nSimulations, self.liqOuterBand, self.rebalForward)

                    positions = Utils.appendPosition(positions, ['time','type','fracSize','low','high','note','tokenAPrice','tokenBPrice', 'cumFees'], [date, 'base',  1, outerLeft, outerRight, 'stop', tokenAPrice, tokenBPrice, fees])
                    end_date = Utils.dtFromMs(Utils.dtToMs(date) + int(self.rebalWindow*60*60*1000)) #convert rebal window to miliseconds and add to current time
                    if (self.verbose):
                        self.logger.info("-"*100);
                        self.logger.info("Position was rebalanced early");
                        self.logger.info("Entering new position on date=%s" % date);
                        self.logger.info("Measurements: close=%.3f, drift=%.4f, diffusion=%.3f" % (close, drift, diffusion));
                        self.logger.info("Paremters: outerLeft=%.2f, stopLeft=%.2f, stopRight=%.2f, outerRight=%.2f" %(outerLeft, stopLeft, stopRight, outerRight));
                        self.logger.info("-"*100);

                else:
                    positions = Utils.appendPosition(positions, ['time','type','fracSize','low','high','note','tokenAPrice','tokenBPrice', 'cumFees'], [date, 'base',  1, outerLeft, outerRight, 'hold', tokenAPrice, tokenBPrice, fees])

            elif date >= end_date:
                # set new position
                # calculate fees during interval
                outerLeft, stopLeft, stopRight, outerRight = Utils.getBands(close, drift, diffusion, self.rebalWindow, self.nSimulations, self.liqOuterBand, self.rebalForward)
                if (self.verbose):
                    self.logger.info("-"*100);
                    self.logger.info("Successfully held position through");
                    self.logger.info("Entering new position on date=%s" % date);
                    self.logger.info("Measurements: close=%.3f, drift=%.4f, diffusion=%.3f" % (close, drift, diffusion));
                    self.logger.info("Paremters: outerLeft=%.2f, stopLeft=%.2f, stopRight=%.2f, outerRight=%.2f" %(outerLeft, stopLeft, stopRight, outerRight));
                    self.logger.info("-"*100);
                positions = Utils.appendPosition(positions, ['time','type','fracSize','low','high','note','tokenAPrice','tokenBPrice','cumFees'], [date, 'base',  1, outerLeft, outerRight, 'new', tokenAPrice, tokenBPrice, fees])
                end_date = Utils.dtFromMs(Utils.dtToMs(date) + int(self.rebalWindow*60*60*1000)) #convert rebal window to miliseconds and add to current time
            else:
                print("data issue");

        positions = pd.DataFrame(positions);
        self.positions = positions;

        return


if __name__ == "__main__":
    parser = configparser.ConfigParser();
    parser.read("../settings.ini");

    logging.basicConfig();
    logging.getLogger().setLevel(logging.INFO);
    algo = UniswapV3LP();
    dataDir = parser.get("Data","DATA_DIR");
    positionsDir = parser.get("Data","POSITIONS_DIR");
    stepInterval = parser.get("Data","TICK_INTERVAL");
    ## cast into minutes
    stepInterval = int(stepInterval.replace("h",""))*60 if "h" in stepInterval else int(stepInterval.replace("m",""))
    for symbol in ["WETHCOMP", "WETHMKR", "WETHUNI", "WETHUSDC", "WETHUSDT", "WETHWBTC"]:

        algo.parseConfig({"symbol": symbol,
                          "sdt": datetime(2021, 1, 1),
                          "edt": datetime(2021, 5, 11),
                          "size": 1,
                          "dataDir": dataDir,
                          "rollingWindow": int(24*30*60/stepInterval), # rollingWindow of 30 days
                          "rebalWindow": int(24*3*60/stepInterval), # rebal at least every 3 days
                          "liqOuterBand": .99, # percentile contained of anticipated forward movements in rebalWindow
                          "rebalForward": .90, # rebalance percentile of anticipated forward movements in rebalWindow
                          "nSimulations": 1000, # for Monte Carlo
                          "useDrift": False, # use drift in monte carlo?
                          "verbose": True # log trades?
                          });

        algo.getData();
        algo.generateSignal();
        algo.generatePositions();
        algo.positions.to_csv(positionsDir + symbol + '.csv');
        algo.pnl = Utils.calculatePnL(algo.positions);
        algo.pnl.to_csv(positionsDir + symbol + '_PnL.csv', index=False);
