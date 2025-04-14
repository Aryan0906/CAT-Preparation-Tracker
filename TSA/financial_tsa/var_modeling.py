import numpy as np
from arch import arch_model

class VaRModel:
    def __init__(self, returns, confidence_level=0.95):
        self.returns = returns
        self.confidence_level = confidence_level
        self.z_score = abs(np.percentile(np.random.standard_normal(10000), 
                                       (1-confidence_level)*100))

    def fit_garch(self):
        """Fit GARCH(1,1) model"""
        model = arch_model(self.returns, vol='Garch', p=1, q=1)
        self.garch_model = model.fit(disp='off')
        return self.garch_model

    def calculate_var(self):
        """Calculate parametric VaR"""
        volatility = np.sqrt(self.garch_model.conditional_volatility[-1])
        var = self.returns.mean() + self.z_score * volatility
        return var

    def historical_var(self):
        """Calculate historical VaR"""
        return np.percentile(self.returns, (1-self.confidence_level)*100)

    def backtest_var(self, var_estimates, actual_returns):
        """Perform Kupiec test for VaR backtesting"""
        violations = (actual_returns < var_estimates).sum()
        n = len(actual_returns)
        expected_violations = n * (1 - self.confidence_level)
        return {
            'violations': violations,
            'expected_violations': expected_violations,
            'violation_ratio': violations/expected_violations
        }