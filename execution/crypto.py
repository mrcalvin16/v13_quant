class CryptoExecutor:
    def __init__(self, config):
        self.client = None

    def submit_order(self, symbol, qty, side):
        return {"message": "Dummy Binance order submitted (testing mode)."}
