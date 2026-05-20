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
                
                for entry in feed.entries[:20]:
                    try:
                        pub_date = datetime(*entry.published_parsed[:6])
                        if pub_date < one_hour_ago:
                            continue
                        
                        title = entry.title.lower()
                        if any(keyword in title for keyword in ['oil', 'crude', 'energy', 'petroleum', 'gas', 'fuel', 'brent', 'wti']):
                            articles.append({
                                'source': 'RSS',
                                'title': entry.title,
                                'link': entry.link,
                                'published': pub_date,
                                'summary': entry.get('summary', '')[:200]
                            })
                    except:
                        continue
            except Exception as e:
                logger.warning(f"Error fetching RSS {feed_url}: {e}")
        
        logger.info(f"Found {len(articles)} oil articles from RSS")
        return articles
    
    def get_oilprice_news(self) -> List[Dict]:
        """Скрейпить новини з OilPrice.com"""
        try:
            logger.debug("Scraping OilPrice.com")
            response = requests.get('https://oilprice.com/', headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            for item in soup.find_all('article')[:15]:
                try:
                    title_elem = item.find('h3') or item.find('h2')
                    link_elem = item.find('a')
                    
                    if title_elem and link_elem:
                        articles.append({
                            'source': 'OilPrice',
                            'title': title_elem.get_text().strip(),
                            'link': link_elem.get('href', ''),
                            'published': datetime.now(),
                        })
                except:
                    continue
            
            logger.info(f"Found {len(articles)} articles from OilPrice")
            return articles
        except Exception as e:
            logger.warning(f"Error scraping OilPrice: {e}")
            return []
    
    def get_trading_economics_news(self) -> List[Dict]:
        """Отримує новини з Trading Economics"""
        try:
            logger.debug("Fetching Trading Economics energy news")
            response = requests.get(
                'https://tradingeconomics.com/commodities',
                headers=self.headers, timeout=self.timeout
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            for link in soup.find_all('a', {'href': lambda x: x and 'oil' in x.lower()})[:10]:
                title = link.get_text().strip()
                if title:
                    articles.append({
                        'source': 'Trading Economics',
                        'title': title,
                        'link': link.get('href', ''),
                        'published': datetime.now(),
                    })
            
            logger.info(f"Found {len(articles)} articles from Trading Economics")
            return articles
        except Exception as e:
            logger.warning(f"Error fetching Trading Economics: {e}")
            return []
    
    def scrape_all_news(self) -> List[Dict]:
        """Збирає всі новини з усіх джерел"""
        all_news = []
        
        logger.info("Starting oil news scraping...")
        
        all_news.extend(self.get_rss_feeds())
        all_news.extend(self.get_oilprice_news())
        all_news.extend(self.get_trading_economics_news())
        
        unique_news = []
        seen_titles = set()
        
        for article in all_news:
            title_lower = article['title'].lower()
            if title_lower not in seen_titles:
                unique_news.append(article)
                seen_titles.add(title_lower)
        
        logger.info(f"Total unique articles: {len(unique_news)}")
        return sorted(unique_news, key=lambda x: x['published'], reverse=True)
