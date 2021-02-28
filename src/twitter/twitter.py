import os
import tweepy as tw


consumer_key= ''
consumer_secret= ''
access_token= ''
access_token_secret= ''


auth = tw.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tw.API(auth, wait_on_rate_limit=True)

contents = "Now that the limit is 280 characters, the most common length of a tweet is 33 characters. Historically, only 9% of tweets hit Twitter's 140-character limit, now it's 1%. That said, Twitter did see some impact from the doubling of character count in terms of how people write."

api.update_status(contents + contents)
