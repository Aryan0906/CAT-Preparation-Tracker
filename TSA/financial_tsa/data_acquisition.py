import yfinance as yf
import pandas as pd
import pandas_datareader.data as web
from datetime import datetime, timedelta

class DataAcquisition:
    def __init__(self):
        self.start_date = datetime.now() - timedelta(days=365*5)  # 5 years of data
        self.end_date = datetime.now()

    def get_stock_data(self, tickers):
        """Pull daily stock prices from Yahoo Finance"""
        df = pd.DataFrame()
        for ticker in tickers:
            stock = yf.Ticker(ticker)
            hist = stock.history(start=self.start_date, end=self.end_date)
            df[ticker] = hist['Close']
        return df

    def get_interest_rates(self):
        """Get Treasury yields from FRED"""
        rates = ['DGS1', 'DGS5', 'DGS10']  # 1,5,10-year Treasury rates
        df = web.DataReader(rates, 'fred', self.start_date, self.end_date)
        return df

    def get_fx_rates(self, pairs=['EURUSD=X', 'GBPUSD=X', 'JPYUSD=X']):
        """Get FX rates from Yahoo Finance"""
        df = pd.DataFrame()
        for pair in pairs:
            fx = yf.Ticker(pair)
            hist = fx.history(start=self.start_date, end=self.end_date)
            df[pair] = hist['Close']
        return df