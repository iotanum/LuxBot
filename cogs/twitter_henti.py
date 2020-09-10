import os

from dotenv import load_dotenv
import tweepy

load_dotenv(dotenv_path="../secrets.env")

CONSUMER_KEY = os.getenv("consumer_key")
CONSUMER_SECRET = os.getenv("consumer_secret")
AUTH_TOKEN = os.getenv("auth_token")
AUTH_SECRET_TOKEN = os.getenv("auth_access_secret_token")
AUTH_BEARER_KEY = os.getenv("auth_bearer_token")


class Twitter:
    def __init__(self):
        self.since_id = None
        self.max_id = None
        self.gathered_tweets = {"max_id": self.max_id,
                                "since_id": self.since_id,
                                "tweet_urls": []}
        self.api = self.get_api_running()

    def get_api_running(self):
        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(AUTH_TOKEN, AUTH_SECRET_TOKEN)

        return tweepy.API(auth, wait_on_rate_limit=True)

    async def _construct_tweet_url(self, tweet):
        return f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id_str}"

    async def _should_ignore(self, tweet):
        to_ignore_patterns = ["ID", "Lv"]

        if any(pattern in tweet.text for pattern in to_ignore_patterns):
            return True

    async def _tweet_has_an_image(self, tweet):
        return True if tweet.entities.get("media") else None

    async def _get_15_home_timeline_tweets(self):
        return self.api.home_timeline(since_id=self.gathered_tweets['since_id'],
                                      max_id=self.gathered_tweets['max_id'],
                                      count=15)

    async def _update_since_or_max_ids(self, tweet, idx):
        if idx == 1:
            self.gathered_tweets['since_id'] = tweet.id_str

    async def get_all_henti_tweets(self):
        homeline_tweets = await self._get_15_home_timeline_tweets()

        for idx, tweet in enumerate(homeline_tweets, 1):
            if await self._tweet_has_an_image(tweet):
                if not await self._should_ignore(tweet):
                    tweet_url = await self._construct_tweet_url(tweet)
                    self.gathered_tweets['tweet_urls'].append(tweet_url)

                    await self._update_since_or_max_ids(tweet, idx)

        return self.gathered_tweets

