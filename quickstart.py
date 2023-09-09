from tweeterpy import TweeterPy
from tweeterpy import config
from tweeterpy.util import find_nested_key


def main():
    #config.TIMEOUT = 5
    #config.PROXY = {'http': 'proxy_here', 'https': 'proxy_here'}
    twitter = TweeterPy()
    print(twitter.get_user_id('elonmusk'))
    print(twitter.get_user_info('elonmusk'))
    # print(twitter.get_user_data('elonmusk'))
    # tweets = twitter.get_user_tweets('elonmusk', total=200)
    # Get all the username from the tweets.
    # usernames = find_nested_key(tweets,"screen_name")
    # print(twitter.get_user_media('elonmusk', total=100))


if __name__ == "__main__":
    main()
