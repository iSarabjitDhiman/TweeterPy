import asyncio

from tweeterpy import TweeterPy, TweeterPyAsync


def main():
    twitter = TweeterPy()
    twitter.initialize(deep_scan=False)
    response = twitter.user_by_screen_name(screen_name="elonmusk")
    print(response)


async def main_async():
    twitter = TweeterPyAsync()
    await twitter.initialize(deep_scan=False)
    response = await twitter.user_by_screen_name(screen_name="elonmusk")
    print(response)


if __name__ == "__main__":
    main()
    asyncio.run(main_async())
