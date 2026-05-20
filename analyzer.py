"""
Technical Analysis Module
EMA, RSI, Volume analysis
"""

import logging
from typing import List, Tuple, Dict, Optional

logger = logging.getLogger(__name__)

def ema(values: List[float], period: int) -> List[float]:
    if len(values) < period:
        return values
    k = 2 / (period + 1)
    result = [values[0]]
    for v in values[1:]:
        result.append(v * k + result[-1] * (1 - k))
    return result

def rsi(closes: List[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

def volume_analysis(volumes: List[float], lookback: int = 20) -> Tuple[float, float]:
    if len(volumes) < lookback:
        lookback = len(volumes)
    vol_avg = sum(volumes[-lookback:]) / lookback
    return volumes[-1], vol_avg

def analyze_signal(
    closes: List[float],
    volumes: List[float],
    ema_fast: int = 9,
    ema_slow: int = 21,
    rsi_period: int = 14,
    rsi_min: int = 35,
    rsi_max: int = 60,
    volume_mult: float = 1.2
) -> Tuple[Optional[str], Dict[str, float]]:
    try:
        ema_fast_vals = ema(closes, ema_fast)
        ema_slow_vals = ema(closes, ema_slow)
        ef, es = ema_fast_vals[-1], ema_slow_vals[-1]
        price = closes[-1]
        rsi_value = rsi(closes, rsi_period)
        vol_cur, vol_avg = volume_analysis(volumes, lookback=20)
        vol_ratio = vol_cur / vol_avg if vol_avg > 0 else 0
        
        meta = {
            "price": round(price, 2),
            "ema_fast": round(ef, 2),
            "ema_slow": round(es, 2),
            "rsi": rsi_value,
            "vol_ratio": round(vol_ratio, 2),
            "ema_fast_period": ema_fast,
            "ema_slow_period": ema_slow,
        }
        
        short_ok = ef < es and rsi_min <= rsi_value <= rsi_max and price < es and vol_ratio > volume_mult
        if short_ok:
            return "SHORT", meta
        
        long_ok = ef > es and rsi_min <= rsi_value <= rsi_max and price > es and vol_ratio > volume_mult
        if long_ok:
            return "LONG", meta
        
        return None, meta
    except Exception as e:
        logger.error(f"Error in analyze_signal: {e}")
        return None, {}