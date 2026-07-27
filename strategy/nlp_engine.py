import yfinance as yf
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import time

class NLPEngine:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        
    def get_news_sentiment(self, ticker: str) -> dict:
        """
        Fetches live news for the ticker and scores the sentiment using VADER NLP.
        Returns a 0-100 score and the top headlines with publisher and link.
        """
        try:
            asset = yf.Ticker(ticker)
            news = asset.news
            
            if not news or len(news) == 0:
                return {"score": 50, "reason": "No recent news found.", "headlines": []}
                
            total_compound = 0
            headlines = []
            
            # Analyze top 5 recent articles
            limit = min(8, len(news))
            for i in range(limit):
                article = news[i]
                title = article.get('title', '')
                if title:
                    sentiment = self.analyzer.polarity_scores(title)
                    total_compound += sentiment['compound']
                    
                    # Convert unix timestamp to readable string if available
                    pub_time = article.get('providerPublishTime', 0)
                    time_str = ""
                    if pub_time:
                        time_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(pub_time))
                        
                    headlines.append({
                        "title": title,
                        "publisher": article.get('publisher', 'News'),
                        "link": article.get('link', '#'),
                        "time": time_str
                    })
            
            # Average compound score (-1 to +1)
            avg_compound = total_compound / limit
            
            # Map -1 to +1 into a 0 to 100 scale
            # If neutral (0), score is 50. If extremely positive (+1), score is 100.
            score = int((avg_compound + 1) * 50)
            
            reason = "News Sentiment is Neutral"
            if score > 65:
                reason = "News Sentiment is Bullish"
            elif score < 35:
                reason = "News Sentiment is Bearish"
                
            return {
                "score": score,
                "reason": reason,
                "headlines": headlines
            }
        except Exception as e:
            return {"score": 50, "reason": f"Error fetching news: {e}", "headlines": []}
