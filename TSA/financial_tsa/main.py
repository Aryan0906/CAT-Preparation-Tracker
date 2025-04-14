from data_acquisition import DataAcquisition
from data_preparation import DataPreparation
from var_modeling import VaRModel
import matplotlib.pyplot as plt
import seaborn as sns

def main():
    # Initialize data acquisition
    da = DataAcquisition()
    
    # Get market data
    stocks = da.get_stock_data(['SPY', 'AGG', 'VEA'])  # Example portfolio
    rates = da.get_interest_rates()
    fx = da.get_fx_rates()

    # Prepare data
    dp = DataPreparation()
    stock_returns = dp.clean_data(stocks)
    
    # Portfolio returns (equal-weighted for example)
    portfolio_returns = stock_returns.mean(axis=1)

    # Check stationarity
    stationarity_result = dp.check_stationarity(portfolio_returns)
    print("Stationarity Test Results:")
    print(stationarity_result)

    # Fit VaR model
    var_model = VaRModel(portfolio_returns)
    garch_result = var_model.fit_garch()
    var_estimate = var_model.calculate_var()
    
    print(f"\nPortfolio 95% VaR: {var_estimate:.2%}")

    # Plot results
    plt.figure(figsize=(15, 8))
    plt.plot(portfolio_returns)
    plt.axhline(y=var_estimate, color='r', linestyle='--', 
                label='95% VaR')
    plt.title('Portfolio Returns with VaR')
    plt.legend()
    plt.show()

if __name__ == "__main__":
    main()