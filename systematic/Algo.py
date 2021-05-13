import logging, sys, pandas as pd

class Algo:

    def init(self):
        self.logger = logging.getLogger('Algo')
        self.data = []
        return

    def parseConfig(self, config):
        """ Parse Input Config """

        ##symbols are formated like EXCHANGE-SYMBOL (exchange specific grammar)
        self.symbol = config["symbol"]
        self.sdt = config["sdt"]
        self.edt = config["edt"]
        self.dataDir = config["dataDir"]

        self.logger.info('Config Parsed')
        return

    def getData(self):
        """ Collect Data -- According to specified symbols and fields """

        df = pd.read_csv(self.dataDir+'/'+self.symbol+'.csv')
        df['time'] = pd.to_datetime(df['time'])
        df.set_index('time', inplace=True)
        self.data = df
        self.logger.info('Data Grab Successful')
        return

    def generateSignal(self):
        """ Signal Generation is Strategy Specific """
        pass

    def constructPortfolio(self):
        """ Position Construction is Strategy Specific """
        pass
