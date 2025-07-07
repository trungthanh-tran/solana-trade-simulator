from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from src.services.trade_service import TradeService
from src.config import TELEGRAM_API_TOKEN
import json
import logging

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

class TelegramBot:
    """Telegram bot for handling CA trading commands."""
    
    def __init__(self):
        self.trade_service = TradeService()
        self.app = Application.builder().token(TELEGRAM_API_TOKEN).build()
        
        # Register command handlers
        self.app.add_handler(CommandHandler("buy", self.buy_ca))
        self.app.add_handler(CommandHandler("sell", self.sell_ca))
        self.app.add_handler(CommandHandler("pnl", self.pnl_ca))
        self.app.add_handler(CommandHandler("sellall", self.sell_all_ca))
        self.app.add_handler(CommandHandler("help", self.help_command)) # Add help command
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /help is issued."""
        help_text = """
Welcome to the CA Trading Bot!

Here are the commands you can use:

/buy <ca_mint> <amount_sol> - Buys a specified amount of a CA (Casting Address) using SOL.
    Example: /buy SomeCAMintAddress 0.1

/sell <ca_mint> <amount_ca> - Sells a specified amount of a CA.
    Example: /sell SomeCAMintAddress 100

/sellall <ca_mint> - Sells all of your holdings for a specific CA.
    Example: /sellall SomeCAMintAddress

/pnl <ca_mint> - Calculates and displays the Profit and Loss (PnL) for a specific CA.
    Example: /pnl SomeCAMintAddress
        """
        await update.message.reply_text(help_text)

    async def buy_ca(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /buy <ca_mint> <amount_sol> command."""
        args = context.args
        if len(args) != 2 or not args[1].replace(".", "").isdigit():
            await update.message.reply_text(
                "Incorrect usage.\n"
                "Usage: `/buy <ca_mint> <amount_sol>`\n"
                "Example: `/buy SomeCAMintAddress 0.1`", 
                parse_mode="Markdown"
            )
            return
        
        ca_mint = args[0].strip()
        try:
            amount_sol = float(args[1])
            if amount_sol <= 0:
                raise ValueError("Amount must be positive.")
        except ValueError:
            await update.message.reply_text("Invalid amount. Please provide a valid positive number for SOL.")
            return
        
        await update.message.reply_text(f"Attempting to buy CA `{ca_mint}` with `{amount_sol}` SOL...", parse_mode="Markdown")
        logger.info(f"User {update.effective_user.id} requested to buy {ca_mint} with {amount_sol} SOL.")

        result = self.trade_service.buy_ca(ca_mint=ca_mint, amount_sol=amount_sol) # , slippage_bps=slippage_bps if you added it

        if result["error_code"] == 0:
            trade_data = result["data"]
            message = (
                f"✅ **Buy successful!**\n"
                f"CA Mint: `{trade_data['ca_mint']}`\n"
                f"Input: `{trade_data['input_amount']:.6f} {trade_data['input_token']}`\n"
                f"Output: `{trade_data['output_amount']:.6f} {trade_data['output_token']}`\n"
                f"Timestamp: `{trade_data['timestamp']}`\n"
                f"Slippage: `{trade_data['slippage_bps']} BPS`"
            )
            await update.message.reply_text(message, parse_mode="Markdown")
        else:
            error_message = result.get("error_message", "An unknown error occurred.")
            message = f"❌ **Buy failed!**\nError: `{error_message}`"
            await update.message.reply_text(message, parse_mode="Markdown")
            logger.error(f"Buy command failed for {ca_mint}: {error_message}")

    async def sell_ca(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /sell <ca_mint> <amount_ca> command."""
        args = context.args
        if len(args) != 2 or not args[1].replace(".", "").isdigit():
            await update.message.reply_text(
                "Incorrect usage.\n"
                "Usage: `/sell <ca_mint> <amount_ca>`\n"
                "Example: `/sell SomeCAMintAddress 100`", 
                parse_mode="Markdown"
            )
            return
        
        ca_mint = args[0].strip()
        try:
            amount_ca = float(args[1])
            if amount_ca <= 0:
                raise ValueError("Amount must be positive.")
        except ValueError:
            await update.message.reply_text("Invalid amount. Please provide a valid positive number for CA.")
            return
        
        logger.info(f"User {update.effective_user.id} requested to sell {amount_ca} of {ca_mint}.")
        await update.message.reply_text(f"Attempting to sell `{amount_ca}` of CA `{ca_mint}`...", parse_mode="Markdown")
        result = self.trade_service.sell_ca(ca_mint=ca_mint, amount_ca=amount_ca)
        if result["error_code"] == 0:
            trade_data = result["data"]
            message = (
                f"✅ **Sell successful!**\n"
                f"CA Mint: `{trade_data['ca_mint']}`\n"
                f"Input: `{trade_data['input_amount']:.6f} {trade_data['input_token']}`\n"
                f"Output: `{trade_data['output_amount']:.6f} {trade_data['output_token']}`\n"
                f"Timestamp: `{trade_data['timestamp']}`\n"
                f"Slippage: `{trade_data['slippage_bps']} BPS`"
            )
            await update.message.reply_text(message, parse_mode="Markdown")
        else:
            error_message = result.get("error_message", "An unknown error occurred.")
            message = f"❌ **Sell failed!**\nError: `{error_message}`"
            await update.message.reply_text(message, parse_mode="Markdown")
            logger.error(f"Sell command failed for {ca_mint}: {error_message}")


    async def sell_all_ca(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /sellall <ca_mint> command."""
        args = context.args
        if len(args) != 1:
            await update.message.reply_text(
                "Incorrect usage.\n"
                "Usage: `/sellall <ca_mint>`\n"
                "Example: `/sellall SomeCAMintAddress`", 
                parse_mode="Markdown"
            )
            return
        
        ca_mint = args[0].strip()
        await update.message.reply_text(f"Attempting to sell all holdings of CA `{ca_mint}`...", parse_mode="Markdown")
        logger.info(f"User {update.effective_user.id} requested to sell all of {ca_mint}.")
        result = self.trade_service.sell_all_ca(ca_mint=ca_mint)
        if result["error_code"] == 0:
            trade_data = result["data"]
            message = (
                f"✅ **Sell all successful!**\n"
                f"CA Mint: `{trade_data['ca_mint']}`\n"
                f"Input: `{trade_data['input_amount']:.6f} {trade_data['input_token']}`\n"
                f"Output: `{trade_data['output_amount']:.6f} {trade_data['output_token']}`\n"
                f"Timestamp: `{trade_data['timestamp']}`\n"
                f"Slippage: `{trade_data['slippage_bps']} BPS`"
            )
            await update.message.reply_text(message, parse_mode="Markdown")
        else:
            error_message = result.get("error_message", "An unknown error occurred.")
            message = f"❌ **Sell all failed!**\nError: `{error_message}`"
            await update.message.reply_text(message, parse_mode="Markdown")
            logger.error(f"Sell all command failed for {ca_mint}: {error_message}")

    async def pnl_ca(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /pnl <ca_mint> command."""
        args = context.args
        if len(args) != 1:
            await update.message.reply_text(
                "Incorrect usage.\n"
                "Usage: `/pnl <ca_mint>`\n"
                "Example: `/pnl SomeCAMintAddress`", 
                parse_mode="Markdown"
            )
            return
        
        ca_mint = args[0].strip()
        await update.message.reply_text(f"Calculating PnL for CA `{ca_mint}`...", parse_mode="Markdown")
        logger.info(f"User {update.effective_user.id} requested PnL for {ca_mint}.")

        result = self.trade_service.calculate_pnl(ca_mint=ca_mint)
        if result["error_code"] == 0:
            pnl_data = result["data"]
            message = (
                f"📊 **PnL for {pnl_data['ca_mint']}**\n"
                f"Total SOL Spent: `{pnl_data['total_sol_spent']:.6f}`\n"
                f"Total CA Bought: `{pnl_data['total_ca_bought']:.6f}`\n"
                f"Total SOL Received: `{pnl_data['total_sol_received']:.6f}`\n"
                f"Total CA Sold: `{pnl_data['total_ca_sold']:.6f}`\n"
                f"Realized PnL: `{pnl_data['realized_pnl']:.6f} SOL`\n"
                f"Unrealized PnL: `{pnl_data['unrealized_pnl']:.6f} SOL`\n"
                f"**Total PnL:** `{pnl_data['total_pnl']:.6f} SOL`"
            )
            await update.message.reply_text(message, parse_mode="Markdown")
        else:
            error_message = result.get("error_message", "An unknown error occurred.")
            message = f"❌ **PnL calculation failed!**\nError: `{error_message}`"
            await update.message.reply_text(message, parse_mode="Markdown")
            logger.error(f"PnL command failed for {ca_mint}: {error_message}")


    def run(self):
        """Start the Telegram bot."""
        self.app.run_polling()