from tweeterpy.schemas.variables.base import TweeterPyVariableSchema
from tweeterpy.schemas.variables.constants import SearchProduct, SearchQuerySource


class HomeTimeline(TweeterPyVariableSchema):
    count: int = 40
    include_promoted_content: bool = True
    latest_control_available: bool = True
    with_community: bool = True


class SearchTimeline(TweeterPyVariableSchema):
    raw_query: str
    count: int = 20
    query_source: SearchQuerySource = SearchQuerySource.TYPED
    product: SearchProduct = SearchProduct.TOP


class ListLatestTweetsTimeline(TweeterPyVariableSchema):
    list_id: str
    count: int = 100


class TopicLandingPage(TweeterPyVariableSchema):
    rest_id: str
    count: int = 100


if __name__ == "__main__":
    pass
