import numpy as np

class Simulator:
    def __init__(self, returns):
        self.returns = returns

    def monte_carlo(self, n_sims=1000, n_days=252):
        simulations = np.zeros((n_sims, n_days))
        for i in range(n_sims):
            simulations[i] = np.random.choice(self.returns, n_days)
        return simulations
