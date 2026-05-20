#!/usr/bin/env python3
"""
News Sentiment Analysis - Аналіз сентименту новин про нафту
"""

import logging
from typing import List, Dict, Tuple
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)

class NewssentimentAnalyzer:
    """Аналізує сентимент новин про нафту"""
    
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
        
        # Ключові слова для посилення сигналів
        self.bullish_keywords = [
            'surge', 'jump', 'rally', 'gain', 'rise', 'up',
            'growth', 'strong', 'boost', 'recover', 'positive',
            'profit', 'demand', 'production', 'export', 'agreement',
            'supply', 'deficit', 'increased', 'higher'
        ]
        
        self.bearish_keywords = [
            'fall', 'drop', 'decline', 'down', 'crash', 'plunge',
            'weakness', 'weak', 'loss', 'negative', 'pressure',
            'oversupply', 'excess', 'inventory', 'glut', 'concern',
            'risk', 'crisis', 'sanction', 'cut', 'lower'
        ]
    
    def analyze_textblob(self, text: str) -> float:
        """Аналіз сентименту за допомогою TextBlob (-1 до 1)"""
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            return polarity
        except:
            return 0.0
    
    def analyze_vader(self, text: str) -> float:
        """Аналіз сентименту за допомогою VADER (-1 до 1)"""
        try:
            scores = self.vader.polarity_scores(text)
            compound = scores['compound']
            return compound
        except:
            return 0.0
    
    def analyze_keywords(self, text: str) -> float:
        """Аналіз за ключовими словами"""
        text_lower = text.lower()
        
        bullish_count = sum(1 for word in self.bullish_keywords if word in text_lower)
        bearish_count = sum(1 for word in self.bearish_keywords if word in text_lower)
        
        if bullish_count + bearish_count == 0:
            return 0.0
        
        return (bullish_count - bearish_count) / (bullish_count + bearish_count)
    
    def analyze_article(self, article: Dict) -> Dict:
        """Комплексний аналіз статті"""
        title = article.get('title', '')
        summary = article.get('summary', '')
        text = f"{title} {summary}"
        
        try:
            textblob_score = self.analyze_textblob(text)
            vader_score = self.analyze_vader(text)
            keyword_score = self.analyze_keywords(text)
            
            # Середнє значення з вагами
            composite_score = (
                textblob_score * 0.3 +
                vader_score * 0.4 +
                keyword_score * 0.3
            )
            
            return {
                'article': article,
                'textblob': round(textblob_score, 3),
                'vader': round(vader_score, 3),
                'keywords': round(keyword_score, 3),
                'composite': round(composite_score, 3),
                'sentiment': 'BULLISH' if composite_score > 0.1 else ('BEARISH' if composite_score < -0.1 else 'NEUTRAL')
            }
        except Exception as e:
            logger.error(f"Error analyzing article: {e}")
            return {
                'article': article,
                'composite': 0.0,
                'sentiment': 'NEUTRAL'
            }
    
    def analyze_batch(self, articles: List[Dict]) -> List[Dict]:
        """Аналіз групи статей"""
        results = []
        for article in articles:
            results.append(self.analyze_article(article))
        return results
    
    def get_sentiment_signal(self, analyzed_articles: List[Dict]) -> Tuple[str, float]:
        """
        Генерує торговельний сигнал на основі аналізованих статей
        Returns: (signal, confidence)
        """
        if not analyzed_articles:
            logger.warning("No analyzed articles")
            return None, 0.0
        
        total_score = sum(art['composite'] for art in analyzed_articles)
        avg_score = total_score / len(analyzed_articles)
        
        bullish_count = sum(1 for art in analyzed_articles if art['sentiment'] == 'BULLISH')
        bearish_count = sum(1 for art in analyzed_articles if art['sentiment'] == 'BEARISH')
        neutral_count = len(analyzed_articles) - bullish_count - bearish_count
        
        confidence = abs(avg_score)
        
        logger.info(f"Sentiment Summary: BULLISH={bullish_count}, BEARISH={bearish_count}, NEUTRAL={neutral_count}")
        logger.info(f"Average score: {avg_score:.3f}, Confidence: {confidence:.3f}")
        
        # Сигнал тільки якщо перевага >50% і середня оцінка значна
        if avg_score > 0.2 and bullish_count > bearish_count:
            return "LONG", min(confidence, 1.0)
        elif avg_score < -0.2 and bearish_count > bullish_count:
            return "SHORT", min(confidence, 1.0)
        else:
            return None, 0.0
