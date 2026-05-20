#!/usr/bin/env python3
"""
Oil News Scraper - Отримання новин про нафту з RSS та веб-сайтів
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict
from bs4 import BeautifulSoup
import feedparser

logger = logging.getLogger(__name__)

class OilNewsScraper:
    """Збирає новини про нафту з різних джерел"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.timeout = 10
    
    def get_rss_feeds(self) -> List[Dict]:
        """Отримує новини з RSS фідів про нафту"""
        feeds = [
            "https://feeds.bloomberg.com/markets/news.rss?topic=energy",
            "https://feeds.reuters.com/reuters/businessNews",
            "https://oilprice.com/rss/news/",
        ]
        
        articles = []
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        
        for feed_url in feeds:
            try:
                logger.debug(f"Fetching RSS: {feed_url}")
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:20]:  # Останні 20 статей
                    try:
                        pub_date = datetime(*entry.published_parsed[:6])
                        
                        # Фільтруємо тільки статті за останню годину
                        if pub_date < one_hour_ago:
                            continue
                        
                        # Перевіряємо чи стаття про нафту
                        title = entry.title.lower()\n                        if any(keyword in title for keyword in ['oil', 'crude', 'energy', 'petroleum', 'gas', 'fuel', 'brent', 'wti']):\n                            articles.append({\n                                'source': 'RSS',\n                                'title': entry.title,\n                                'link': entry.link,\n                                'published': pub_date,\n                                'summary': entry.get('summary', '')[:200]\n                            })\n                    except:\n                        continue\n            except Exception as e:\n                logger.warning(f"Error fetching RSS {feed_url}: {e}")\n        
        logger.info(f"Found {len(articles)} oil articles from RSS")\n        return articles\n    \n    def get_oilprice_news(self) -> List[Dict]:\n        """Скрейпить новини з OilPrice.com\"\"\"\n        try:\n            logger.debug("Scraping OilPrice.com")\n            response = requests.get('https://oilprice.com/', headers=self.headers, timeout=self.timeout)\n            response.raise_for_status()\n            \n            soup = BeautifulSoup(response.content, 'html.parser')\n            articles = []\n            \n            # OilPrice структура може змінюватися\n            for item in soup.find_all('article')[:15]:\n                try:\n                    title_elem = item.find('h3') or item.find('h2')\n                    link_elem = item.find('a')\n                    \n                    if title_elem and link_elem:\n                        articles.append({\n                            'source': 'OilPrice',\n                            'title': title_elem.get_text().strip(),\n                            'link': link_elem.get('href', ''),\n                            'published': datetime.now(),\n                        })\n                except:\n                    continue\n            \n            logger.info(f"Found {len(articles)} articles from OilPrice")\n            return articles\n        except Exception as e:\n            logger.warning(f"Error scraping OilPrice: {e}")\n            return []\n    \n    def get_trading_economics_news(self) -> List[Dict]:\n        """Отримує новини з Trading Economics\"\"\"\n        try:\n            logger.debug("Fetching Trading Economics energy news")\n            response = requests.get(\n                'https://tradingeconomics.com/commodities'\n                headers=self.headers, timeout=self.timeout\n            )\n            response.raise_for_status()\n            \n            soup = BeautifulSoup(response.content, 'html.parser')\n            articles = []\n            \n            # Пошук новин про енергію/нафту\n            for link in soup.find_all('a', {'href': lambda x: x and 'oil' in x.lower()})[:10]:\n                title = link.get_text().strip()\n                if title:\n                    articles.append({\n                        'source': 'Trading Economics',\n                        'title': title,\n                        'link': link.get('href', ''),\n                        'published': datetime.now(),\n                    })\n            \n            logger.info(f"Found {len(articles)} articles from Trading Economics")\n            return articles\n        except Exception as e:\n            logger.warning(f"Error fetching Trading Economics: {e}")\n            return []\n    \n    def scrape_all_news(self) -> List[Dict]:\n        \"\"\"Збирає всі новини з усіх джерел\"\"\"\n        all_news = []\n        \n        logger.info("Starting oil news scraping...")\n        \n        all_news.extend(self.get_rss_feeds())\n        all_news.extend(self.get_oilprice_news())\n        all_news.extend(self.get_trading_economics_news())\n        \n        # Видаляємо дублікати за заголовком\n        unique_news = []\n        seen_titles = set()\n        \n        for article in all_news:\n            title_lower = article['title'].lower()\n            if title_lower not in seen_titles:\n                unique_news.append(article)\n                seen_titles.add(title_lower)\n        \n        logger.info(f"Total unique articles: {len(unique_news)}\")\n        return sorted(unique_news, key=lambda x: x['published'], reverse=True)\n