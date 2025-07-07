CA Trading
A Python project to simulate buying and selling CA tokens against SOL on the Solana blockchain, using Jupiter's V6 Quote API. Trades are stored in a SQLite database, and Profit and Loss (PnL) is calculated. Includes a Telegram bot for interacting via /buy ca, /sell ca, and /pnl ca commands.
Setup

Install dependencies:
pip install -r requirements.txt


Configure:

Edit config/config.properties:
Set db_file (default: sqlite:///trades.db).
Set api_token with your Telegram bot token (obtain from BotFather).


Example:[Database]
db_file=sqlite:///trades.db

[Telegram]
api_token=YOUR_TELEGRAM_BOT_TOKEN




Run:
python main.py


Interact via Telegram:

Start a chat with your bot.
Use commands:
/buy ca <ca_mint> <amount_sol>: Buy CA tokens with SOL.
/sell ca <ca_mint> <amount_ca>: Sell CA tokens for SOL.
/pnl ca <ca_mint>: Calculate PnL for a CA token.


Example: /buy ca 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU 1.0



Structure

config/: Configuration files (e.g., config.properties).
src/: Source code.
models/: SQLAlchemy models (e.g., trade.py).
services/: Business logic (e.g., trade_service.py).
bot/: Telegram bot logic (e.g., telegram_bot.py).
config.py: Loads configuration.


tests/: Unit tests.
main.py: Entry point.
requirements.txt: Dependencies.
README.md: This file.

Notes

Simulates trades using Jupiter's Quote API (https://quote-api.jup.ag/v6/quote).
Stores trades in a SQLite database using SQLAlchemy.
Calculates realized and unrealized PnL in SOL.
Assumes 9 decimals for tokens; adjust for other tokens.
For actual trading, integrate with Jupiter's swap API and a Solana wallet.

Running Tests
python -m unittest discover tests
