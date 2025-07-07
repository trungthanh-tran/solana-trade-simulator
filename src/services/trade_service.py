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
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to fetch quote: {str(e)}"}

    def buy_ca(self, ca_mint: str, amount_sol: float, slippage_bps: int = 50) -> dict:
        """
        Simulate a /buy CA command and store trade data in SQLite.
        """
        sol_mint = "So11111111111111111111111111111111111111112"
        quote = self.get_quote(input_mint=sol_mint, output_mint=ca_mint, amount=amount_sol, slippage_bps=slippage_bps)
        
        if "error" in quote:
            return quote
        
        out_amount = int(quote.get("outAmount", 0)) / 10**9
        trade = {
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
                type=trade["type"],
                ca_mint=trade["ca_mint"],
                input_token=trade["input_token"],
                input_amount=trade["input_amount"],
                output_token=trade["output_token"],
                output_amount=trade["output_amount"],
                timestamp=datetime.now(),
                slippage_bps=trade["slippage_bps"]
            )
            session.add(trade_entry)
            session.commit()
        
        return trade

    def sell_ca(self, ca_mint: str, amount_ca: float, slippage_bps: int = 50) -> dict:
        """
        Simulate a /sell CA command and store trade data in SQLite.
        """
        sol_mint = "So11111111111111111111111111111111111111112"
        quote = self.get_quote(input_mint=ca_mint, output_mint=sol_mint, amount=amount_ca, slippage_bps=slippage_bps)
        
        if "error" in quote:
            return quote
        
        out_amount = int(quote.get("outAmount", 0)) / 10**9
        trade = {
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
                type=trade["type"],
                ca_mint=trade["ca_mint"],
                input_token=trade["input_token"],
                input_amount=trade["input_amount"],
                output_token=trade["output_token"],
                output_amount=trade["output_amount"],
                timestamp=datetime.now(),
                slippage_bps=trade["slippage_bps"]
            )
            session.add(trade_entry)
            session.commit()
        
        return trade

    def calculate_pnl(self, ca_mint: str) -> dict:
        """
        Calculate realized and unrealized PnL for a specific CA token.
        """
        with self.Session() as session:
            ca_trades = session.query(Trade).filter(Trade.ca_mint == ca_mint).all()
        
        if not ca_trades:
            return {"error": "No trades found for this CA token."}
        
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
        realized_pnl = total_sol_received - (total_sol_spent * (total_ca_sold / total_ca_bought if total_ca_bought > 0 else 0))
        
        # Unrealized PnL: Current value of remaining CA minus cost of remaining CA
        remaining_ca = total_ca_bought - total_ca_sold
        if remaining_ca > 0:
            quote = self.get_quote(input_mint=ca_mint, output_mint="So11111111111111111111111111111111111111112", amount=remaining_ca)
            if "error" in quote:
                unrealized_pnl = 0.0
            else:
                current_sol_value = int(quote.get("outAmount", 0)) / 10**9
                avg_buy_price = total_sol_spent / total_ca_bought if total_ca_bought > 0 else 0
                unrealized_pnl = current_sol_value - (avg_buy_price * remaining_ca)
        else:
            unrealized_pnl = 0.0
        
        return {
            "ca_mint": ca_mint,
            "total_sol_spent": total_sol_spent,
            "total_ca_bought": total_ca_bought,
            "total_sol_received": total_sol_received,
            "total_ca_sold": total_ca_sold,
            "realized_pnl": realized_pnl,
            "unrealized_pnl": unrealized_pnl,
            "total_pnl": realized_pnl + unrealized_pnl
        }