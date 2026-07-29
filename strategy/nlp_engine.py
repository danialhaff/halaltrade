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
                
                # Support for new and old yfinance news formats
                if 'content' in article:
                    content = article['content']
                    title = content.get('title', '')
                    # Convert pubDate to readable time
                    pub_time = content.get('pubDate', '')
                    time_str = pub_time[:10] if pub_time else ""
                    publisher = content.get('provider', {}).get('displayName', 'News')
                    link_obj = content.get('clickThroughUrl') or content.get('canonicalUrl') or {}
                    link = link_obj.get('url', '#')
                else:
                    title = article.get('title', '')
                    pub_time = article.get('providerPublishTime', 0)
                    time_str = ""
                    if pub_time:
                        time_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(pub_time))
                    publisher = article.get('publisher', 'News')
                    link = article.get('link', '#')

                if title:
                    sentiment = self.analyzer.polarity_scores(title)
                    total_compound += sentiment['compound']

                    # Generate AI Remark based on Sentiment and Keywords
                    title_lower = title.lower()
                    effect = "Neutral impact expected."
                    if "rate" in title_lower or "fed" in title_lower or "inflation" in title_lower or "cpi" in title_lower:
                        effect = "High volatility expected. Impacts rate-sensitive assets."
                    elif "earnings" in title_lower or "revenue" in title_lower:
                        effect = "Sector-specific volatility based on earnings surprise."
                    elif "war" in title_lower or "geopolitical" in title_lower or "strike" in title_lower:
                        effect = "Negative for equities. Bullish for commodities (Gold/Oil)."
                    elif sentiment['compound'] > 0.4:
                        effect = "Bullish sentiment. Positive momentum expected."
                    elif sentiment['compound'] < -0.4:
                        effect = "Bearish sentiment. Downside risk alert."

                    headlines.append({
                        "title": title,
                        "publisher": publisher,
                        "link": link,
                        "time": time_str,
                        "effect": effect
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
