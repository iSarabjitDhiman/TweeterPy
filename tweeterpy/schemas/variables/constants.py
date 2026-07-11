import random
from enum import Enum

from typing_extensions import Self


class TweetReferrer(Enum):
    HOME = "home"
    PROFILE = "profile"
    TWEET = "tweet"
    # NOTIFICATION = "notification"
    # TIMELINE = "timeline"

    @classmethod
    def random(cls) -> Self:
        return random.choice(list(cls))


class SearchProduct(Enum):
    TOP = "Top"
    LATEST = "Latest"
    LIST = "Lists"
    MEDIA = "Media"
    PEOPLE = "People"
    PHOTOS = "Photos"
    VIDEOS = "Videos"


class SearchQuerySource(Enum):
    ADVANCED_SEARCH_PAGE = "advanced_search_page"
    CASHTAG_CLICK = "cashtag_click"
    HASHTAG_CLICK = "hashtag_click"
    PROMOTED_TREND_CLICK = "promoted_trend_click"
    RECENT_SEARCH_CLICK = "recent_search_click"
    RELATED_QUERY_CLICK = "related_query_click"
    SPELLING_CORRECTION_CLICK = "spelling_correction_click"
    SPELLING_CORRECTION_REVERT_CLICK = "spelling_suggestion_revert_click"
    SPELLING_EXPANSION_CLICK = "spelling_expansion_click"
    SPELLING_EXPANSION_REVERT_CLICK = "spelling_expansion_revert_click"
    SPELLING_SUGGESTION_CLICK = "spelling_suggestion_click"
    TREND_CLICK = "trend_click"
    TREND_VIEW = "trend_view"
    TYPEAHEAD_CLICK = "typeahead_click"
    TYPED = "typed_query"
    TV_SEARCH = "TvSearch"
    TWEET_DETAIL_QUOTE_TWEET = "tdqt"
    TWEET_DETAIL_SIMILAR_POST = "tweet_detail_similar_posts"


class TweetRankingMode(Enum):
    RELEVANCE = "Relevance"
    # CHRONOLOGICAL = "Chronological"


if __name__ == "__main__":
    pass
