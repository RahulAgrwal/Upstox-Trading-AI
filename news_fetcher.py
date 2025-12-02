from newsapi import NewsApiClient
from datetime import datetime, timedelta

from logger_config import get_logger
logger = get_logger(__name__)
class NewsFetcher:
    """
    Wrapper class for NewsAPI to fetch and filter stock or company news.
    """

    def __init__(self, api_key: str, top_headlines_limit: int = 5):
        """Initialize the NewsFetcher with your NewsAPI key."""
        self.client = NewsApiClient(api_key=api_key)
        self.top_headlines_limit = top_headlines_limit

    def get_company_news(self, query: str, days: int = 7, language: str = 'en', limit: int = 10):
        """
        Fetch recent news articles related to a company or stock.

        Args:
            query (str): Company or stock name (e.g. 'Infosys' or 'Tesla').
            days (int): Number of past days to search for news.
            language (str): Language filter for news articles.
            limit (int): Maximum number of articles to return.

        Returns:
            list: A list of dictionaries with title, source, date, and url.
        """
        logger.info(f"Fetching news for {query}")
        from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        to_date = datetime.now().strftime('%Y-%m-%d')

        try:
            response = self.client.get_everything(
                q=query,
                language=language,
                from_param=from_date,
                to=to_date,
                sort_by='relevancy',
                page_size=self.top_headlines_limit
            )

            articles = response.get('articles', [])
            results = []

            for article in articles:
                results.append({
                    'title': article['title'],
                    'description': article['description'],
                    'source': article['source']['name'],
                    'published_at': article['publishedAt']
                })
            results.sort(
                            key=lambda x: datetime.fromisoformat(x['published_at'].replace('Z', '+00:00')),
                            reverse=True
                        )
            logger.info(f"Found {len(results)} news articles for {query} : {results}")
            return results

        except Exception as e:
            logger.info(f"❌ Error fetching news: {e}")
            return []

    def get_top_headlines(self, category: str = 'business', country: str = 'in'):
        """
        Fetch top business headlines (default India).

        Args:
            category (str): News category (business, tech, sports, etc.).
            country (str): Country code (e.g. 'in' for India, 'us' for USA).

        Returns:
            list: A list of top headlines with title, source, and url.
        """
        try:
            response = self.client.get_top_headlines(
                category=category,
                country=country,
                page_size=self.top_headlines_limit
            )

            articles = response.get('articles', [])
            return [
                {
                    'title': a['title'],
                    'description': a['description'],
                    'source': a['source']['name'],
                    'published_at': a['publishedAt']
                }
                for a in articles
            ]

        except Exception as e:
            logger.info(f"❌ Error fetching top headlines: {e}")
            return []
