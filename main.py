import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from src.bot.telegram_bot import TelegramBot

def main():
    # Initialize and run Telegram bot
    bot = TelegramBot()
    bot.run()

if __name__ == "__main__":
    main()