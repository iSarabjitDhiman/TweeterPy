from setuptools import setup

VERSION = "1.0.16"
SHORT_DESCRIPTION = "TweeterPy is a python library to extract data from Twitter. TweeterPy API lets you scrape data from a user's profile like username, userid, bio, followers/followings list, profile media, tweets, etc."

with open("requirements.txt") as file:
    dependencies = file.read().splitlines()
with open("README.md", "r") as file:
    DESCRIPTION = file.read()


setup(
    name="tweeterpy",
    version=VERSION,
    description=SHORT_DESCRIPTION,
    long_description=DESCRIPTION,
    long_description_content_type="text/markdown",
    author="Sarabjit Dhiman",
    author_email="hello@sarabjitdhiman.com",
    license="MIT",
    url="https://github.com/iSarabjitDhiman/TweeterPy",
    packages=["tweeterpy"],
    keywords=["tweeterpy", "twitter scraper", "tweet scraper",
              "twitter data extraction", "twitter api",
              "twitter python", "tweet api", "tweetpy"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Unix",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Build Tools",
        "Programming Language :: Python :: 3",
    ],
    install_requires=dependencies,
    python_requires=">=3"
)
