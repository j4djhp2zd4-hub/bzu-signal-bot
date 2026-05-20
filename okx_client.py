"""
OKX API Client
"""

import requests
import logging
from typing import Tuple, List, Optional

logger = logging.getLogger(__name__)

class OKXClient:
    BASE_URL = "https://www.okx.com/api/v5/market"
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
    
    def get_candles(
        self,
        instrument: str,
        bar: str = "15m",
        limit: int = 50
    ) -> Tuple[Optional[List[float]], Optional[List[float]]]:
        try:
            url = f"{self.BASE_URL}/candles"
            params = {"instId": instrument, "bar": bar, "limit": str(limit)}
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != "0":
                logger.error(f"OKX API error: {data.get('msg')}")
                return None, None
            
            candles = sorted(data.get("data", []), key=lambda x: int(x[0]))
            closes, volumes = [], []
            
            for candle in candles:
                try:
                    closes.append(float(candle[4]))
                    volumes.append(float(candle[5]))
                except (ValueError, IndexError):
                    continue
            
            if len(closes) < 10:
                logger.warning(f"Not enough candles: {len(closes)}")
                return None, None
            
            logger.info(f"Fetched {len(closes)} candles for {instrument}")
            return closes, volumes
        except Exception as e:
            logger.error(f"Error fetching candles: {e}")
            return None, None