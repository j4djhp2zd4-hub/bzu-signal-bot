#!/usr/bin/env python3

import os
import sys
import logging
from datetime import datetime, timezone

from okx_client import OKXClient
from analyzer import analyze_signal, ema, rsi, volume_analysis

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Отримуємо дані
okx = OKXClient(timeout=10)
closes, volumes = okx.get_candles("BZ-USDT-SWAP", "15m", 50)

if closes and volumes:
    logger.info("=" * 80)
    logger.info("DEBUG INFO")
    logger.info("=" * 80)
    
    # Розраховуємо індикатори
    ema9_vals = ema(closes, 9)
    ema21_vals = ema(closes, 21)
    rsi14 = rsi(closes, 14)
    vol_cur, vol_avg = volume_analysis(volumes)
    
    ema9 = ema9_vals[-1]
    ema21 = ema21_vals[-1]
    price = closes[-1]
    vol_ratio = vol_cur / vol_avg
    
    logger.info(f"Price: {price:.2f}")
    logger.info(f"EMA9: {ema9:.2f}")
    logger.info(f"EMA21: {ema21:.2f}")
    logger.info(f"EMA9 > EMA21? {ema9 > ema21} (LONG condition)")
    logger.info(f"RSI: {rsi14:.2f}")
    logger.info(f"RSI between 35-60? {35 <= rsi14 <= 60}")
    logger.info(f"Price > EMA21? {price > ema21} (LONG condition)")
    logger.info(f"Volume ratio: {vol_ratio:.2f}x")
    logger.info(f"Volume > 1.2x? {vol_ratio > 1.2}")
    logger.info("=" * 80)
    
    # Генеруємо сигнал
    signal, meta = analyze_signal(closes, volumes)
    logger.info(f"SIGNAL: {signal}")
    logger.info("=" * 80)
else:
    logger.error("Failed to fetch candles")
