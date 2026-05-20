#!/usr/bin/env python3
"""
Oil News Signal Bot - Основний бот з аналізом новин
"""

import os
import sys
import logging
from datetime import datetime, timezone

from oil_news_scraper import OilNewsScraper
from news_sentiment import NewssentimentAnalyzer
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
        "balance": float(os.environ.get("BALANCE", "5.0")),
        "leverage": int(os.environ.get("LEVERAGE", "20")),
        "risk_percent": float(os.environ.get("RISK_PERCENT", "0.20")),
        "stop_loss_percent": float(os.environ.get("STOP_LOSS_PERCENT", "0.018")),
        "tp1_percent": float(os.environ.get("TP1_PERCENT", "0.030")),
        "tp2_percent": float(os.environ.get("TP2_PERCENT", "0.055")),
        "cooldown_minutes": int(os.environ.get("COOLDOWN_MINUTES", "30")),
        "news_threshold": float(os.environ.get("NEWS_THRESHOLD", "0.2")),
    }

def validate_config(config):
    required = ["telegram_token", "telegram_chat_id"]
    missing = [key for key in required if not config.get(key)]
    if missing:
        logger.error(f"Missing: {', '.join(missing)}")
        return False
    return True

def get_current_price():
    """Отримуємо поточну ціну BZ-USDT"""
    try:
        from okx_client import OKXClient
        okx = OKXClient(timeout=10)
        closes, _ = okx.get_candles("BZ-USDT-SWAP", "1m", 1)
        if closes:
            return closes[-1]
    except:
        pass
    return None

def main():
    logger.info("=" * 80)
    logger.info("Oil News Signal Bot started")
    logger.info("=" * 80)
    
    config = load_config()
    if not validate_config(config):
        return 1
    
    logger.info(f"Config: {config['instrument']}")
    logger.info(f"News threshold: {config['news_threshold']}")
    
    try:
        # Шаг 1: Збираємо новини
        logger.info("Step 1: Scraping oil news...")
        scraper = OilNewsScraper()
        news_articles = scraper.scrape_all_news()
        
        if not news_articles:
            logger.warning("No news found in the last hour")
            logger.info("=" * 80)
            return 0
        
        logger.info(f"Found {len(news_articles)} news articles")
        
        # Шаг 2: Аналізуємо сентимент
        logger.info("Step 2: Analyzing sentiment...")
        analyzer = NewssentimentAnalyzer()
        analyzed_news = analyzer.analyze_batch(news_articles)
        
        # Показуємо топ новини
        sorted_by_sentiment = sorted(analyzed_news, key=lambda x: x['composite'], reverse=True)
        logger.info("Top 3 articles:")
        for i, art in enumerate(sorted_by_sentiment[:3], 1):
            logger.info(f"  {i}. [{art['sentiment']}] {art['article']['title'][:60]}... (score: {art['composite']})")
        
        # Шаг 3: Генерує��о сигнал
        logger.info("Step 3: Generating signal...")
        signal, confidence = analyzer.get_sentiment_signal(analyzed_news)
        
        logger.info(f"Signal: {signal}, Confidence: {confidence:.3f}")
        
        # Шаг 4: Перевіряємо cooldown
        telegram = TelegramSender(config["telegram_token"], config["telegram_chat_id"])
        state_mgr = SignalState(cooldown_minutes=config["cooldown_minutes"])
        
        if signal and confidence >= config["news_threshold"]:
            logger.info(f"Signal meets threshold ({confidence:.3f} >= {config['news_threshold']})")
            
            if state_mgr.is_signal_allowed(signal):
                # Отримуємо поточну ціну
                price = get_current_price()
                if not price:
                    logger.warning("Could not get current price")
                    price = 0.0
                
                logger.info(f"Sending {signal} at price ${price}...")
                meta = {
                    'ema_fast': 0,
                    'ema_slow': 0,
                    'ema_fast_period': 9,
                    'ema_slow_period': 21,
                    'rsi': 50,
                    'vol_ratio': 1.0,
                    'price': price,
                    'news_confidence': confidence
                }
                
                success = telegram.send_signal(
                    signal=signal, price=price, meta=meta,
                    balance=config["balance"], leverage=config["leverage"],
                    risk_pct=config["risk_percent"],
                    sl_pct=config["stop_loss_percent"],
                    tp1_pct=config["tp1_percent"],
                    tp2_pct=config["tp2_percent"],
                    instrument=config["instrument"],
                )
                
                if success:
                    logger.info(f"✓ {signal} sent successfully")
                    state_mgr.record_signal(signal)
                else:
                    logger.error(f"Failed to send {signal}")
                    return 1
            else:
                logger.info(f"{signal} in cooldown")
        else:
            logger.info(f"Signal does not meet threshold or no signal generated")
            logger.info(f"Confidence: {confidence:.3f}, Threshold: {config['news_threshold']}")
        
        logger.info("=" * 80)
        logger.info("Bot finished")
        logger.info("=" * 80)
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
