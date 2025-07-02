from alpaca_trade_api import REST

class EquityExecutor:
    def __init__(self, config):
        self.api = REST(
            config["key_id"],
            config["secret_key"],
            base_url=config["base_url"]
        )

    def submit_order(self, symbol, qty, side, order_type="market"):
        order = self.api.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type=order_type,
            time_in_force="day"
        )
        return order
