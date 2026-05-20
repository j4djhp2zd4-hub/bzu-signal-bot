#!/usr/bin/env python3
"""
BZU Signal Bot
"""

import os
import sys
import logging
from datetime import datetime, timezone

from okx_client import OKXClient
from analyzer import analyze_signal
from telegram_sender import TelegramSender
from signal_state import SignalState

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def load_config():
    return {
        "telegram_token": os.environ.get("TELEGRAM_TOKEN"),
        "telegram_chat_id": os.environ.get("TELEGRAM_CHAT_ID"),
        "instrument": os.environ.get("INSTRUMENT", "BZ-USDT-SWAP"),
        "bar": os.environ.get("BAR", "15m"),
        "balance": float(os.environ.get("BALANCE", "5.0")),
        "leverage": int(os.environ.get("LEVERAGE", "20")),
        "risk_percent": float(os.environ.get("RISK_PERCENT", "0.20")),
        "stop_loss_percent": float(os.environ.get("STOP_LOSS_PERCENT", "0.018")),
        "tp1_percent": float(os.environ.get("TP1_PERCENT", "0.030")),
        "tp2_percent": float(os.environ.get("TP2_PERCENT", "0.055")),
        "ema_fast": int(os.environ.get("EMA_FAST", "9")),
        "ema_slow": int(os.environ.get("EMA_SLOW", "21")),
        "rsi_period": int(os.environ.get("RSI_PERIOD", "14")),
        "rsi_min": int(os.environ.get("RSI_MIN", "35")),
        "rsi_max": int(os.environ.get("RSI_MAX", "60")),
        "volume_mult": float(os.environ.get("VOLUME_MULT", "1.2")),
        "send_status": os.environ.get("SEND_STATUS", "true").lower() == "true",
        "cooldown_minutes": int(os.environ.get("COOLDOWN_MINUTES", "30")),
    }

def validate_config(config):
    required = ["telegram_token", "telegram_chat_id"]
    missing = [key for key in required if not config.get(key)]
    if missing:
        logger.error(f"Missing: {', '.join(missing)}")
        return False
    return True

def main():
    logger.info("=" * 80)
    logger.info("BZU Signal Bot started")
    logger.info("=" * 80)
    
    config = load_config()
    if not validate_config(config):
        return 1
    
    logger.info(f"Config: {config['instrument']} {config['bar']}")
    
    try:
        logger.info("Fetching candles...")
        okx = OKXClient(timeout=10)
        closes, volumes = okx.get_candles(
            instrument=config["instrument"],
            bar=config["bar"],
            limit=50
        )
        
        if not closes or not volumes:
            logger.error("Failed to fetch candles")
            return 1
        
        logger.info(f"Got {len(closes)} candles")
        logger.info("Analyzing...")
        signal, meta = analyze_signal(
            closes=closes, volumes=volumes,
            ema_fast=config["ema_fast"], ema_slow=config["ema_slow"],
            rsi_period=config["rsi_period"], rsi_min=config["rsi_min"],
            rsi_max=config["rsi_max"], volume_mult=config["volume_mult"],
        )
        
        telegram = TelegramSender(config["telegram_token"], config["telegram_chat_id"])
        state_mgr = SignalState(cooldown_minutes=config["cooldown_minutes"])
        
        if signal:
            logger.info(f"Signal: {signal}")
            if state_mgr.is_signal_allowed(signal):
                logger.info(f"Sending {signal}...")
                success = telegram.send_signal(
                    signal=signal, price=meta["price"], meta=meta,
                    balance=config["balance"], leverage=config["leverage"],
                    risk_pct=config["risk_percent"],
                    sl_pct=config["stop_loss_percent"],
                    tp1_pct=config["tp1_percent"],
                    tp2_pct=config["tp2_percent"],
                    instrument=config["instrument"],
                )
                if success:
                    logger.info(f"✓ {signal} sent")
                    state_mgr.record_signal(signal)
                else:
                    logger.error(f"Failed to send {signal}")
                    return 1
            else:
                logger.info(f"{signal} in cooldown")
        else:
            logger.info("No signal")
            if config["send_status"] and datetime.now(timezone.utc).minute <= 2:
                logger.info("Sending status...")
                telegram.send_status(meta["price"], meta["rsi"], config["instrument"])
        
        logger.info("=" * 80)
        logger.info("Bot finished")
        logger.info("=" * 80)
        return 0
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())