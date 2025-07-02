import requests

class OptionsExecutor:
    def __init__(self, config):
        self.token = config["access_token"]

    def submit_order(self, symbol, qty, side):
        url = "https://api.tradier.com/v1/accounts/{account_id}/orders"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json"
        }
        payload = {
            "class": "option",
            "symbol": symbol,
            "side": side,
            "quantity": qty,
            "type": "market",
            "duration": "day"
        }
        response = requests.post(url, headers=headers, data=payload)
        return response.json()
