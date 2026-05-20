"""
Telegram Notification Module
"""

import requests
import logging
from typing import Dict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class TelegramSender:
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"
    
    def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {"chat_id": self.chat_id, "text": text, "parse_mode": parse_mode}
            requests.post(url, json=payload, timeout=10)
            logger.info("Message sent to Telegram")
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def send_signal(
        self, signal: str, price: float, meta: Dict, balance: float = 5.0,
        leverage: int = 20, risk_pct: float = 0.20, sl_pct: float = 0.018,
        tp1_pct: float = 0.030, tp2_pct: float = 0.055,
        instrument: str = "BZ-USDT-SWAP"
    ) -> bool:
        try:
            now = datetime.now(timezone.utc).strftime("%d.%m %H:%M UTC")
            if signal == "SHORT":
                sl = round(price * (1 + sl_pct), 2)
                tp1 = round(price * (1 - tp1_pct), 2)
                tp2 = round(price * (1 - tp2_pct), 2)
                emoji, label = "🔴", "SHORT"
            else:
                sl = round(price * (1 - sl_pct), 2)
                tp1 = round(price * (1 + tp1_pct), 2)
                tp2 = round(price * (1 + tp2_pct), 2)
                emoji, label = "🟢", "LONG"
            
            margin = round(balance * risk_pct, 2)
            position = round(margin * leverage, 2)
            msg = (
                f"{emoji} *{label}*  |  `{instrument}`\n"
                f"🕐 {now}\n━━━━━━━━━━━━━━━━\n"
                f"💵 Вхід: *${price}*\n🛡 Стоп-лос: *${sl}*\n"
                f"🎯 TP1: *${tp1}* _(50%)_\n🎯 TP2: *${tp2}* _(решта)_\n━━━━━━━━━━━━━━━━\n"
                f"EMA{meta.get('ema_fast_period', 9)}: {meta['ema_fast']}  EMA{meta.get('ema_slow_period', 21)}: {meta['ema_slow']}\n"
                f"RSI: {meta['rsi']}   Обсяг: ×{meta['vol_ratio']}\n━━━━━━━━━━━━━━━━\n"
                f"Маржа: ${margin}  Позиція: ${position}  (×{leverage})\n"
                f"⚠️ Виставляй стоп в OKX одразу!"
            )
            return self.send_message(msg)
        except Exception as e:
            logger.error(f"Error in send_signal: {e}")
            return False
    
    def send_status(self, price: float, rsi: float, instrument: str = "BZ-USDT-SWAP") -> bool:
        try:
            now = datetime.now(timezone.utc).strftime("%H:%M UTC")
            msg = f"⏳ *Немає сигналу*  |  {now}\n`{instrument}` ${price}   RSI: {rsi}"
            return self.send_message(msg)
        except Exception as e:
            logger.error(f"Error in send_status: {e}")
            return False