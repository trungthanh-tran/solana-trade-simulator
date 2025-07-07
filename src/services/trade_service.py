import requests
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.trade import Trade, Base
from src.config import DB_FILE

# Jupiter V6 Quote API endpoint
QUOTE_API_URL = "https://quote-api.jup.ag/v6/quote"

class TradeService:
    """Service for handling CA trades and PnL calculations."""

    def __init__(self):
        self.engine = create_engine(DB_FILE)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def get_quote(self, input_mint: str, output_mint: str, amount: float, slippage_bps: int = 50) -> dict:
        """
        Fetch a swap quote from Jupiter API.
        Returns:
            dict: A dictionary containing 'error_code' (0 for success, -1 for error)
                  and 'data' (quote details) or 'error_message'.
        """
        amount_lamports = int(amount * 10**9)
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": amount_lamports,
            "slippageBps": slippage_bps
        }
        try:
            response = requests.get(QUOTE_API_URL, params=params)
            response.raise_for_status()
            return {"error_code": 0, "data": response.json()}
        except requests.exceptions.RequestException as e:
            return {"error_code": -1, "error_message": f"Failed to fetch quote: {str(e)}"}

    def get_total_ca_held(self, ca_mint: str) -> dict:
        """
        Calculate the total CA tokens held for a given mint address.
        Returns:
            dict: A dictionary containing 'error_code' (0 for success, -1 for error)
                  and 'data' (total CA held) or 'error_message'.
        """
        try:
            with self.Session() as session:
                ca_trades = session.query(Trade).filter(Trade.ca_mint == ca_mint).all()

            total_ca_bought = sum(trade.output_amount for trade in ca_trades if trade.type == "buy")
            total_ca_sold = sum(trade.input_amount for trade in ca_trades if trade.type == "sell")
            return {"error_code": 0, "data": total_ca_bought - total_ca_sold}
        except Exception as e:
            return {"error_code": -1, "error_message": f"Failed to calculate total CA held: {str(e)}"}

    def buy_ca(self, ca_mint: str, amount_sol: float, slippage_bps: int = 50) -> dict:
        """
        Simulate a /buy CA command and store trade data in SQLite.
        Returns:
            dict: A dictionary containing 'error_code' (0 for success, -1 for error)
                  and 'data' (trade details) or 'error_message'.
        """
        sol_mint = "So11111111111111111111111111111111111111112"
        quote_result = self.get_quote(input_mint=sol_mint, output_mint=ca_mint, amount=amount_sol, slippage_bps=slippage_bps)

        if quote_result["error_code"] == -1:
            return quote_result # Pass through the error from get_quote

        quote = quote_result["data"]

        try:
            out_amount = int(quote.get("outAmount", 0)) / 10**9
            trade_data = {
                "type": "buy",
                "ca_mint": ca_mint,
                "input_token": "SOL",
                "input_amount": amount_sol,
                "output_token": "CA",
                "output_amount": out_amount,
                "timestamp": datetime.now().isoformat(),
                "slippage_bps": slippage_bps
            }

            with self.Session() as session:
                trade_entry = Trade(
                    type=trade_data["type"],
                    ca_mint=trade_data["ca_mint"],
                    input_token=trade_data["input_token"],
                    input_amount=trade_data["input_amount"],
                    output_token=trade_data["output_token"],
                    output_amount=trade_data["output_amount"],
                    timestamp=datetime.now(),
                    slippage_bps=trade_data["slippage_bps"]
                )
                session.add(trade_entry)
                session.commit()

            return {"error_code": 0, "data": trade_data}
        except Exception as e:
            return {"error_code": -1, "error_message": f"Failed to process buy CA command: {str(e)}"}

    def sell_ca(self, ca_mint: str, amount_ca: float, slippage_bps: int = 50) -> dict:
        """
        Simulate a /sell CA command and store trade data in SQLite.
        Returns:
            dict: A dictionary containing 'error_code' (0 for success, -1 for error)
                  and 'data' (trade details) or 'error_message'.
        """
        sol_mint = "So11111111111111111111111111111111111111112"
        quote_result = self.get_quote(input_mint=ca_mint, output_mint=sol_mint, amount=amount_ca, slippage_bps=slippage_bps)

        if quote_result["error_code"] == -1:
            return quote_result # Pass through the error from get_quote

        quote = quote_result["data"]

        try:
            out_amount = int(quote.get("outAmount", 0)) / 10**9
            trade_data = {
                "type": "sell",
                "ca_mint": ca_mint,
                "input_token": "CA",
                "input_amount": amount_ca,
                "output_token": "SOL",
                "output_amount": out_amount,
                "timestamp": datetime.now().isoformat(),
                "slippage_bps": slippage_bps
            }

            with self.Session() as session:
                trade_entry = Trade(
                    type=trade_data["type"],
                    ca_mint=trade_data["ca_mint"],
                    input_token=trade_data["input_token"],
                    input_amount=trade_data["input_amount"],
                    output_token=trade_data["output_token"],
                    output_amount=trade_data["output_amount"],
                    timestamp=datetime.now(),
                    slippage_bps=trade_data["slippage_bps"]
                )
                session.add(trade_entry)
                session.commit()

            return {"error_code": 0, "data": trade_data}
        except Exception as e:
            return {"error_code": -1, "error_message": f"Failed to process sell CA command: {str(e)}"}

    def sell_all_ca(self, ca_mint: str, slippage_bps: int = 50) -> dict:
        """
        Simulate a /sellall CA command to sell all held CA tokens for a given mint address.
        Returns:
            dict: A dictionary containing 'error_code' (0 for success, -1 for error)
                  and 'data' (trade details) or 'error_message'.
        """
        total_ca_held_result = self.get_total_ca_held(ca_mint)
        if total_ca_held_result["error_code"] == -1:
            return total_ca_held_result # Pass through error from get_total_ca_held

        total_ca_held = total_ca_held_result["data"]

        if total_ca_held <= 0:
            return {"error_code": -1, "error_message": f"No CA tokens held for mint {ca_mint}."}

        return self.sell_ca(ca_mint=ca_mint, amount_ca=total_ca_held, slippage_bps=slippage_bps)

    def calculate_pnl(self, ca_mint: str) -> dict:
        """
        Calculate realized and unrealized PnL for a specific CA token.
        Returns:
            dict: A dictionary containing 'error_code' (0 for success, -1 for error)
                  and 'data' (PnL details) or 'error_message'.
        """
        try:
            with self.Session() as session:
                ca_trades = session.query(Trade).filter(Trade.ca_mint == ca_mint).all()

            if not ca_trades:
                return {"error_code": -1, "error_message": "No trades found for this CA token."}

            total_sol_spent = 0.0
            total_ca_bought = 0.0
            total_sol_received = 0.0
            total_ca_sold = 0.0

            for trade in ca_trades:
                if trade.type == "buy":
                    total_sol_spent += trade.input_amount
                    total_ca_bought += trade.output_amount
                elif trade.type == "sell":
                    total_sol_received += trade.output_amount
                    total_ca_sold += trade.input_amount

            # Realized PnL: SOL from sales minus SOL spent on corresponding buys
            # This calculation needs to be more robust for partial sells (e.g., using FIFO/LIFO or average cost)
            # For simplicity, assuming average cost for realized PnL for sold portion
            cost_of_sold_ca = total_sol_spent * (total_ca_sold / total_ca_bought if total_ca_bought > 0 else 0)
            realized_pnl = total_sol_received - cost_of_sold_ca

            # Unrealized PnL: Current value of remaining CA minus cost of remaining CA
            remaining_ca = total_ca_bought - total_ca_sold
            unrealized_pnl = 0.0

            if remaining_ca > 0:
                sol_mint = "So11111111111111111111111111111111111111112"
                quote_result = self.get_quote(input_mint=ca_mint, output_mint=sol_mint, amount=remaining_ca)
                if quote_result["error_code"] == -1:
                    # Log the error, but for PnL calculation, we might proceed with 0 unrealized PnL or indicate a partial error
                    unrealized_pnl = 0.0 # Cannot get a quote, so unrealized PnL is 0 for now
                else:
                    current_sol_value = int(quote_result["data"].get("outAmount", 0)) / 10**9
                    avg_buy_price = total_sol_spent / total_ca_bought if total_ca_bought > 0 else 0
                    cost_of_remaining_ca = avg_buy_price * remaining_ca
                    unrealized_pnl = current_sol_value - cost_of_remaining_ca

            return {
                "error_code": 0,
                "data": {
                    "ca_mint": ca_mint,
                    "total_sol_spent": total_sol_spent,
                    "total_ca_bought": total_ca_bought,
                    "total_sol_received": total_sol_received,
                    "total_ca_sold": total_ca_sold,
                    "realized_pnl": realized_pnl,
                    "unrealized_pnl": unrealized_pnl,
                    "total_pnl": realized_pnl + unrealized_pnl
                }
            }
        except Exception as e:
            return {"error_code": -1, "error_message": f"Failed to calculate PnL: {str(e)}"}