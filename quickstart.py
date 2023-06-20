from tweeterpy import TweeterPy


def main():
    twitter = TweeterPy()
    print(twitter.get_user_id('elonmusk'))
    print(twitter.get_user_info('elonmusk'))
    # print(twitter.get_user_data('elonmusk'))
    # print(twitter.get_user_tweets('elonmusk', total=200))
    # print(twitter.get_user_media('elonmusk', total=100))


if __name__ == "__main__":
    main()
