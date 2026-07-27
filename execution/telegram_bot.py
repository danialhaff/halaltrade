import asyncio
from telegram import Bot
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

class TelegramNotifier:
    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        if self.token:
            self.bot = Bot(token=self.token)
        else:
            self.bot = None

    async def send_signal(self, ticker: str, action: str, price: float, qty: float, tier: str, analysis: dict):
        """
        Sends a comprehensive trade proposal to the user's Telegram.
        """
        if not self.bot or not self.chat_id:
            print("Telegram not configured. Signal not sent.")
            return

        signal_str = analysis['signal']
        icon = "🚀" if signal_str == "STRONG BUY" else "🚨"
        
        # Calculate Target Profit and Stop Loss prices
        # Default TP/SL based on tier (High risk = wider stops, Low risk = tighter stops)
        tp_pct, sl_pct = 0.08, 0.03 # Default Low Risk
        if tier == 'Medium': tp_pct, sl_pct = 0.15, 0.05
        elif tier == 'High': tp_pct, sl_pct = 0.30, 0.10
        
        tp_price = price * (1 + tp_pct)
        sl_price = price * (1 - sl_pct)

        message = (
            f"{icon} **{signal_str} SIGNAL** {icon}\n"
            f"**Asset:** {ticker} @ ${price:.2f}\n"
            f"**Risk Tier:** {tier}\n\n"
            f"📊 **Conviction Score: {analysis['conviction']}%**\n"
            f"• Technical: {analysis['technical_score']}% ({analysis['technical_reason']})\n"
            f"• Fundamental: {analysis['fundamental_score']}% ({analysis['fundamental_reason']})\n"
            f"• Sentiment: {analysis['sentiment_score']}% ({analysis['sentiment_reason']})\n\n"
            f"🎯 **Target Profit:** +{tp_pct*100:.1f}% (${tp_price:.2f})\n"
            f"🛑 **Stop Loss:** -{sl_pct*100:.1f}% (${sl_price:.2f})\n\n"
            f"Reply 'APPROVE {ticker}' in the console to execute."
        )
        
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message, parse_mode='Markdown')
            print(f"-> Telegram notification sent to {self.chat_id}")
        except Exception as e:
            print(f"Failed to send Telegram message: {e}")

    def send_signal_sync(self, *args, **kwargs):
        """Helper to run the async send_signal from synchronous code."""
        asyncio.run(self.send_signal(*args, **kwargs))
