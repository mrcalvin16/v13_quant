class UnifiedExecutor:
    def __init__(self, equity_executor, crypto_executor, options_executor):
        self.equity = equity_executor
        self.crypto = crypto_executor
        self.options = options_executor

    def submit_order(self, asset_type, symbol, qty, side, order_type="market"):
        if asset_type == "equity":
            return self.equity.submit_order(symbol, qty, side, order_type)
        elif asset_type == "crypto":
            return self.crypto.submit_order(symbol, qty, side)
        elif asset_type == "option":
            return self.options.submit_order(symbol, qty, side)
        else:
            raise ValueError(f"Unknown asset type: {asset_type}")
