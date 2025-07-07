from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from src.services.trade_service import TradeService
from src.config import TELEGRAM_API_TOKEN
import json

class TelegramBot:
    """Telegram bot for handling CA trading commands."""
    
    def __init__(self):
        self.trade_service = TradeService()
        self.app = Application.builder().token(TELEGRAM_API_TOKEN).build()
        
        # Register command handlers
        self.app.add_handler(CommandHandler("buy", self.buy_ca))
        self.app.add_handler(CommandHandler("sell", self.sell_ca))
        self.app.add_handler(CommandHandler("pnl", self.pnl_ca))
    
    async def buy_ca(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /buy ca <ca_mint> <amount_sol> command."""
        args = context.args
        if len(args) != 2 or not args[0].startswith("ca") or not args[1].replace(".", "").isdigit():
            await update.message.reply_text("Usage: /buy ca <ca_mint> <amount_sol>")
            return
        
        ca_mint = args[0].split("ca")[1].strip()
        try:
            amount_sol = float(args[1])
            if amount_sol <= 0:
                raise ValueError("Amount must be positive.")
        except ValueError:
            await update.message.reply_text("Invalid amount. Please provide a valid number.")
            return
        
        result = self.trade_service.buy_ca(ca_mint=ca_mint, amount_sol=amount_sol)
        if "error" in result:
            await update.message.reply_text(f"Error: {result['error']}")
        else:
            await update.message.reply_text(f"Buy CA Result:\n```json\n{json.dumps(result, indent=2)}\n```", parse_mode="Markdown")

    async def sell_ca(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /sell ca <ca_mint> <amount_ca> command."""
        args = context.args
        if len(args) != 2 or not args[0].startswith("ca") or not args[1].replace(".", "").isdigit():
            await update.message.reply_text("Usage: /sell ca <ca_mint> <amount_ca>")
            return
        
        ca_mint = args[0].split("ca")[1].strip()
        try:
            amount_ca = float(args[1])
            if amount_ca <= 0:
                raise ValueError("Amount must be positive.")
        except ValueError:
            await update.message.reply_text("Invalid amount. Please provide a valid number.")
            return
        
        result = self.trade_service.sell_ca(ca_mint=ca_mint, amount_ca=amount_ca)
        if "error" in result:
            await update.message.reply_text(f"Error: {result['error']}")
        else:
            await update.message.reply_text(f"Sell CA Result:\n```json\n{json.dumps(result, indent=2)}\n```", parse_mode="Markdown")

    async def pnl_ca(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /pnl ca <ca_mint> command."""
        args = context.args
        if len(args) != 1 or not args[0].startswith("ca"):
            await update.message.reply_text("Usage: /pnl ca <ca_mint>")
            return
        
        ca_mint = args[0].split("ca")[1].strip()
        result = self.trade_service.calculate_pnl(ca_mint=ca_mint)
        if "error" in result:
            await update.message.reply_text(f"Error: {result['error']}")
        else:
            await update.message.reply_text(f"PnL Result:\n```json\n{json.dumps(result, indent=2)}\n```", parse_mode="Markdown")

    def run(self):
        """Start the Telegram bot."""
        self.app.run_polling()