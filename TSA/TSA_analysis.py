import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_squared_error
from math import sqrt

# Data Loading and Preprocessing
def load_data(path):
    df = pd.read_csv(path)
    df.columns = ['Date', 'Number of Passengers']
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    return df

# Time Series Components Analysis
def decompose_series(df):
    decomposition = seasonal_decompose(df['Number of Passengers'], period=12)
    
    plt.figure(figsize=(15, 10))
    plt.subplot(411)
    plt.plot(df['Number of Passengers'], label='Original')
    plt.legend(loc='best')
    plt.subplot(412)
    plt.plot(decomposition.trend, label='Trend')
    plt.legend(loc='best')
    plt.subplot(413)
    plt.plot(decomposition.seasonal, label='Seasonal')
    plt.legend(loc='best')
    plt.subplot(414)
    plt.plot(decomposition.resid, label='Residual')
    plt.legend(loc='best')
    plt.tight_layout()
    plt.show()

# Stationarity Test
def check_stationarity(timeseries):
    result = adfuller(timeseries)
    print('ADF Statistic:', result[0])
    print('p-value:', result[1])
    print('Critical values:')
    for key, value in result[4].items():
        print('\t%s: %.3f' % (key, value))

# ARIMA Modeling and Forecasting
def fit_arima_model(data, order):
    model = ARIMA(data, order=order)
    results = model.fit()
    return results

def main():
    # Load data
    df = load_data('AirPassengers.csv')
    
    # Basic visualization
    plt.figure(figsize=(15,5))
    plt.plot(df['Number of Passengers'])
    plt.title('Air Passengers Time Series')
    plt.show()
    
    # Decompose series
    decompose_series(df)
    
    # Check stationarity
    print("Stationarity Test Results:")
    check_stationarity(df['Number of Passengers'])
    
    # Fit ARIMA model
    model = fit_arima_model(df['Number of Passengers'], order=(1,1,1))
    print("\nARIMA Model Summary:")
    print(model.summary())
    
    # Make predictions
    forecast = model.forecast(steps=12)
    print("\nNext 12 months forecast:")
    print(forecast)

if __name__ == "__main__":
    main()