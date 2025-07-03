import os
from alpaca_trade_api.rest import REST, TimeFrame

class EquitiesExecutor:
    def __init__(self):
        """
        Initializes the Alpaca REST API client using environment variables.
        """
        self.api = REST(
            key_id=os.getenv("ALPACA_API_KEY"),
            secret_key=os.getenv("ALPACA_SECRET_KEY"),
            base_url=os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        )

    def submit_order(self, symbol, qty, side, order_type="market", time_in_force="day", limit_price=None):
        """
        Submits an order to Alpaca.

        Args:
            symbol (str): Ticker symbol (e.g., "AAPL")
            qty (float): Quantity to buy or sell
            side (str): "buy" or "sell"
            order_type (str): "market" or "limit"
            time_in_force (str): "day", "gtc", etc.
            limit_price (float): For limit orders
        Returns:
            dict: API response
        """
        if order_type == "limit" and limit_price is None:
            raise ValueError("limit_price must be set for limit orders")

        order_params = {
            "symbol": symbol,
            "qty": qty,
            "side": side,
            "type": order_type,
            "time_in_force": time_in_force
        }
        if order_type == "limit":
            order_params["limit_price"] = limit_price

        order = self.api.submit_order(**order_params)
        return {
            "id": order.id,
            "symbol": order.symbol,
            "qty": order.qty,
            "side": order.side,
            "status": order.status
        }

    def get_position(self, symbol):
        """
        Retrieves the current position in a given symbol.

        Args:
            symbol (str): Ticker symbol
        Returns:
            dict: Position details
        """
        try:
            pos = self.api.get_position(symbol)
            return {
                "symbol": pos.symbol,
                "qty": pos.qty,
                "avg_entry_price": pos.avg_entry_price,
                "unrealized_pl": pos.unrealized_pl,
                "market_value": pos.market_value
            }
        except Exception:
            # If no position exists
            return {
                "symbol": symbol,
                "qty": 0,
                "avg_entry_price": None,
                "unrealized_pl": 0,
                "market_value": 0
            }

    def get_last_trade_price(self, symbol):
        """
        Gets the most recent trade price for a symbol.

        Args:
            symbol (str): Ticker
        Returns:
            float: Last trade price
        """
        trade = self.api.get_last_trade(symbol)
        return float(trade.price)

    def cancel_all_orders(self):
        """
        Cancels all open orders.
        """
        self.api.cancel_all_orders()
