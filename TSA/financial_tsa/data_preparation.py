import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.seasonal import seasonal_decompose

class DataPreparation:
    @staticmethod
    def clean_data(df):
        """Handle missing values and outliers"""
        # Forward fill missing values
        df = df.fillna(method='ffill')
        # Calculate log returns
        returns = np.log(df/df.shift(1))
        return returns.dropna()

    @staticmethod
    def check_stationarity(series):
        """Perform ADF test"""
        result = adfuller(series.dropna())
        return {
            'adf_statistic': result[0],
            'p_value': result[1],
            'critical_values': result[4]
        }

    @staticmethod
    def decompose_series(series, period=252):  # 252 trading days
        """Decompose time series"""
        decomposition = seasonal_decompose(series, period=period)
        return {
            'trend': decomposition.trend,
            'seasonal': decomposition.seasonal,
            'residual': decomposition.resid
        }