from typing import List

from pydantic import Field

from tweeterpy.schemas.variables.base import TweeterPyVariableSchema


class ProfileSpotlightsQuery(TweeterPyVariableSchema):
    screen_name: str = Field(
        serialization_alias="screen_name", validation_alias="screen_name"
    )


class UserByRestId(TweeterPyVariableSchema):
    user_id: str
    with_safety_mode_user_fields: bool = True


class UsersByRestIds(TweeterPyVariableSchema):
    user_ids: List[str]


class UserByScreenName(TweeterPyVariableSchema):
    screen_name: str = Field(
        serialization_alias="screen_name", validation_alias="screen_name"
    )
    with_safety_mode_user_fields: bool = True


class BizProfileFetchUser(TweeterPyVariableSchema):
    rest_id: str


class ConnectionNetwork(TweeterPyVariableSchema):
    """Reusable baseline variable structural layout for Followers, Following, and Mutuals connections."""

    user_id: str
    count: int = 100
    include_promoted_content: bool = False


class Viewer(TweeterPyVariableSchema):
    with_communities_memberships: bool = True
    with_subscribed_tab: bool = True
    with_communities_creation: bool = True


Followers = ConnectionNetwork
Following = ConnectionNetwork
FollowersYouKnow = ConnectionNetwork

if __name__ == "__main__":
    pass
