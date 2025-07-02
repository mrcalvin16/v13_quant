from binance.client import Client

class CryptoExecutor:
    def __init__(self, config):
        self.client = Client(config["api_key"], config["api_secret"])

    def submit_order(self, symbol, qty, side):
        order = self.client.create_order(
            symbol=symbol,
            side=side.upper(),
            type="MARKET",
            quantity=qty
        )
        return order
