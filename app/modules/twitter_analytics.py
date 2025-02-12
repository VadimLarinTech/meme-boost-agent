import tweepy

class TwitterAnalytics:
    def __init__(self, config):
        self.client = tweepy.Client(bearer_token=config['TWITTER_BEARER_TOKEN'])
        self.query = config.get('TWITTER_QUERY', 'crypto')  

    def fetch_and_analyze(self):
        max_retries = 5
        delay = 60 

        for attempt in range(max_retries):
            try:
                response = self.client.search_recent_tweets(
                    query=self.query,
                    max_results=10,
                    tweet_fields=["public_metrics", "lang", "author_id"],
                    expansions=["author_id"],
                    user_fields=["public_metrics"]
                )
                tweets = response.data

                if not tweets:
                    print("Нет найденных твитов.")
                    return {}

                users = {}
                if response.includes and 'users' in response.includes:
                    for user in response.includes['users']:
                        users[user.id] = user

                viral_tweets = []

                for tweet in tweets:
                    tweet_metrics = tweet.public_metrics
                    author = users.get(tweet.author_id)
                    if not author:
                        continue
                    user_metrics = author.public_metrics
                    followers_count = user_metrics.get('followers_count', 0)
                    
                    if followers_count == 0:
                        continue

                    retweet_ratio = tweet_metrics.get('retweet_count', 0) / followers_count
                    like_ratio = tweet_metrics.get('like_count', 0) / followers_count

                    # Пример условия для определения "вирального" твита:
                    # Если соотношение ретвитов или лайков превышает заданный порог (например, 0.1 = 10%)
                    if retweet_ratio >= 0.1 or like_ratio >= 0.1:
                        viral_tweets.append({
                            'tweet_id': tweet.id,
                            'text': tweet.text,
                            'retweet_count': tweet_metrics.get('retweet_count', 0),
                            'like_count': tweet_metrics.get('like_count', 0),
                            'followers_count': followers_count,
                            'retweet_ratio': retweet_ratio,
                            'like_ratio': like_ratio
                        })

                analytics_data = {
                    'query': self.query,
                    'tweets_count': len(tweets),
                    'viral_tweets': viral_tweets
                }

                return analytics_data

            except tweepy.TweepyException as e:
                if '429' in str(e):
                    print(f"Лимит запросов превышен. Ожидание {delay} секунд перед повторной попыткой...")
                    time.sleep(delay)
                    delay *= 2  # экспоненциальное увеличение задержки
                else:
                    print("Ошибка при подключении к Twitter API:", e)
                    return {}

