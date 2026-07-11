from pydantic import Field

from tweeterpy.schemas.variables.base import TweeterPyVariableSchema
from tweeterpy.schemas.variables.constants import TweetRankingMode, TweetReferrer


class UserMedia(TweeterPyVariableSchema):
    user_id: str
    count: int = 100
    include_promoted_content: bool = True
    with_client_event_token: bool = False
    with_birdwatch_notes: bool = False
    with_voice: bool = True
    with_v2_timeline: bool = True


class UserTweets(TweeterPyVariableSchema):
    user_id: str
    count: int = 100
    include_promoted_content: bool = True
    with_quick_promote_eligibility_tweet_fields: bool = True
    with_voice: bool = True
    with_v2_timeline: bool = True


class UserTweetsAndReplies(TweeterPyVariableSchema):
    user_id: str
    count: int = 20
    include_promoted_content: bool = True
    with_community: bool = True
    with_voice: bool = True
    with_v2_timeline: bool = True


class TweetResultByRestId(TweeterPyVariableSchema):
    tweet_id: str
    with_birdwatch_notes: bool = True
    with_community: bool = False
    include_promoted_content: bool = False
    with_voice: bool = False


class TweetDetail(TweeterPyVariableSchema):
    focal_tweet_id: str
    referrer: TweetReferrer = Field(default_factory=TweetReferrer.random)
    ranking_mode: TweetRankingMode = TweetRankingMode.RELEVANCE
    with_rux_injections: bool = Field(
        False,
        serialization_alias="with_rux_injections",
        validation_alias="with_rux_injections",
    )
    include_promoted_content: bool = True
    with_community: bool = True
    with_quick_promote_eligibility_tweet_fields: bool = True
    with_article_rich_content: bool = False
    with_birdwatch_notes: bool = True
    with_voice: bool = True
    with_v2_timeline: bool = True


class Likes(TweeterPyVariableSchema):
    user_id: str
    count: int = 100
    include_promoted_content: bool = False
    with_client_event_token: bool = False
    with_birdwatch_notes: bool = False
    with_voice: bool = True
    with_v2_timeline: bool = True


class EngagementTimeline(TweeterPyVariableSchema):
    """Reusable baseline variable structural layout for Favoriters, Retweeters etc."""

    tweet_id: str
    count: int = 100
    include_promoted_content: bool = True


class UserHighlightsTweets(TweeterPyVariableSchema):
    user_id: str
    count: int = 100
    include_promoted_content: bool = True
    with_voice: bool = True


Favoriters = EngagementTimeline
Retweeters = EngagementTimeline

if __name__ == "__main__":
    pass
