import logging.config
import random
from typing import Any, Dict, List, Optional, Union

from bs4 import BeautifulSoup
from x_client_transaction import ClientTransaction

from tweeterpy.constants import LOGGING_CONFIG
from tweeterpy.core.definition import APIDefinition
from tweeterpy.core.migration import XMigrationHandler
from tweeterpy.core.resources import XOperations, XUrls
from tweeterpy.core.session import AsyncSession, Session, TweeterPySession
from tweeterpy.schemas import Operation
from tweeterpy.services.parser import APIParser
from tweeterpy.services.updater import APIUpdater
from tweeterpy.utils.text import parse_html

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


class TweeterPyClient:
    def __init__(
        self, session: TweeterPySession, definitions: Optional[APIDefinition] = None
    ) -> None:
        self.session = session
        self.parser = APIParser()
        self.updater = APIUpdater(session=session)
        self.api_definitions = definitions or APIDefinition()

    @property
    def is_logged_in(self) -> bool:
        return all(k in self.session.cookies for k in ("auth_token", "ct0"))

    @property
    def me(self):
        return self.viewer

    @property
    def viewer(self):
        variables = {
            "withCommunitiesMemberships": True,
            "withSubscribedTab": True,
            "withCommunitiesCreation": True,
        }
        return self.execute(operation=XOperations.Viewer.name, variables=variables)

    def _apply_updates(
        self,
        home_page: Union[BeautifulSoup, Any],
        ondemand_file_response: str,
        new_definitions: Dict[str, Any],
    ):
        """Shared logic to update state from fetched data."""

        # Update API Definitions
        self.api_definitions.update(
            features=new_definitions.get("features", {}),
            operations=new_definitions.get("operations", {}),
        )

        # Initialize ClientTransaction for x-client-transaction-id generation
        try:
            self.session.client_transaction = ClientTransaction(
                home_page_response=parse_html(home_page),
                ondemand_file_response=ondemand_file_response,
            )
        except Exception as error:
            logger.warning(f"Could not initialize ClientTransaction: {error}")

    def execute(
        self,
        operation: Union[Operation, str],
        variables: Optional[Dict[str, Any]] = None,
    ):
        if isinstance(operation, str):
            operation = self.api_definitions.create_operation(
                operation_name=operation, variables=variables
            )

        url = (
            operation.url
            or f"{XUrls.GRAPHQL_BASE}/{operation.query_id}/{operation.name}"
        )
        params = operation.payload if operation.method == "GET" else None
        json = operation.payload if operation.method == "POST" else None

        return self.session.request(
            url=url, method=operation.method, params=params, json=json
        )

    def profile_spotlights_query(self, username: str):
        variables = {"screen_name": username}
        return self.execute(
            operation=XOperations.ProfileSpotlightsQuery.name, variables=variables
        )

    def user_by_rest_id(self, user_id: str):
        variables = {"userId": user_id, "withSafetyModeUserFields": True}
        return self.execute(
            operation=XOperations.UserByRestId.name, variables=variables
        )

    def users_by_rest_ids(self, user_ids: List[str]):
        variables = {"userIds": user_ids}
        return self.execute(
            operation=XOperations.UsersByRestIds.name, variables=variables
        )

    def user_by_screen_name(self, screen_name: str):
        variables = {"screen_name": screen_name, "withSafetyModeUserFields": True}
        return self.execute(
            operation=XOperations.UserByScreenName.name, variables=variables
        )

    def user_media(self, user_id: str, total: int = 100):
        variables = {
            "userId": user_id,
            "count": total,
            "includePromotedContent": True,
            "withClientEventToken": False,
            "withBirdwatchNotes": False,
            "withVoice": True,
            "withV2Timeline": True,
        }
        return self.execute(operation=XOperations.UserMedia.name, variables=variables)

    def user_tweets(self, user_id: str, total: int = 100):
        variables = {
            "userId": user_id,
            "count": total,
            "includePromotedContent": True,
            "withQuickPromoteEligibilityTweetFields": True,
            "withVoice": True,
            "withV2Timeline": True,
        }
        return self.execute(operation=XOperations.UserTweets.name, variables=variables)

    def user_tweets_and_replies(self, user_id: str, total: int = 20):
        variables = {
            "userId": user_id,
            "count": total,
            "includePromotedContent": True,
            "withCommunity": True,
            "withVoice": True,
            "withV2Timeline": True,
        }
        return self.execute(
            operation=XOperations.UserTweetsAndReplies.name, variables=variables
        )

    def tweet_result_by_rest_id(self, tweet_id: str):
        variables = {
            "tweetId": tweet_id,
            "withBirdwatchNotes": True,
            "withCommunity": False,
            "includePromotedContent": False,
            "withVoice": False,
        }
        return self.execute(
            operation=XOperations.TweetResultByRestId.name, variables=variables
        )

    def tweet_detail(self, tweet_id: str):
        referer = random.choice(["home", "profile", "tweet"])
        variables = {
            "focalTweetId": tweet_id,
            "referrer": referer,
            "rankingMode": "Relevance",
            "with_rux_injections": False,
            "includePromotedContent": True,
            "withCommunity": True,
            "withQuickPromoteEligibilityTweetFields": True,
            "withArticleRichContent": False,
            "withBirdwatchNotes": True,
            "withVoice": True,
            "withV2Timeline": True,
        }

        return self.execute(operation=XOperations.TweetDetail.name, variables=variables)

    def likes(self, user_id: str, total: int = 100):
        variables = {
            "userId": user_id,
            "count": total,
            "includePromotedContent": False,
            "withClientEventToken": False,
            "withBirdwatchNotes": False,
            "withVoice": True,
            "withV2Timeline": True,
        }
        return self.execute(operation=XOperations.Likes.name, variables=variables)

    def home_timeline(self, total: int = 40):
        variables = {
            "count": total,
            "includePromotedContent": True,
            "latestControlAvailable": True,
            "withCommunity": True,
        }
        return self.execute(
            operation=XOperations.HomeTimeline.name, variables=variables
        )

    def list_latest_tweets_timeline(self, list_id: str, total: int = 100):
        variables = {"listId": list_id, "count": total}
        return self.execute(
            operation=XOperations.ListLatestTweetsTimeline.name, variables=variables
        )

    def topic_landing_page(self, topic_id: str, total: int = 100):
        variables = {"rest_id": topic_id, "count": total}
        return self.execute(
            operation=XOperations.TopicLandingPage.name, variables=variables
        )

    def followers(self, user_id: str, total: int = 100):
        variables = {"userId": user_id, "count": total, "includePromotedContent": False}
        return self.execute(operation=XOperations.Followers.name, variables=variables)

    def following(self, user_id: str, total: int = 100):
        variables = {"userId": user_id, "count": total, "includePromotedContent": False}
        return self.execute(operation=XOperations.Following.name, variables=variables)

    def followers_you_know(self, user_id: str, total: int = 100):
        variables = {"userId": user_id, "count": total, "includePromotedContent": False}
        return self.execute(
            operation=XOperations.FollowersYouKnow.name, variables=variables
        )

    def biz_profile_fetch_user(self, user_id: int):
        variables = {"rest_id": user_id}
        return self.execute(
            operation=XOperations.BizProfileFetchUser.name, variables=variables
        )

    def favoriters(self, tweet_id: str, total: int = 100):
        variables = {
            "tweetId": tweet_id,
            "count": total,
            "includePromotedContent": True,
        }
        return self.execute(operation=XOperations.Favoriters.name, variables=variables)

    def retweeters(self, tweet_id: str, total: int = 100):
        variables = {
            "tweetId": tweet_id,
            "count": total,
            "includePromotedContent": True,
        }
        return self.execute(operation=XOperations.Retweeters.name, variables=variables)

    def user_highlights_tweets(self, user_id: int, total: int = 100):
        variables = {
            "userId": user_id,
            "count": total,
            "includePromotedContent": True,
            "withVoice": True,
        }
        return self.execute(
            operation=XOperations.UserHighlightsTweets.name, variables=variables
        )

    def search(self, query: str, search_filter: str = "Top", total: int = 20):
        variables = {
            "rawQuery": query,
            "count": total,
            "querySource": "typed_query",
            "product": search_filter,
        }
        return self.execute(
            operation=XOperations.SearchTimeline.name, variables=variables
        )


class TweeterPy(TweeterPyClient):
    def __init__(
        self,
        session: Optional[TweeterPySession] = None,
        definitions: Optional[APIDefinition] = None,
    ) -> None:
        if session is None:
            session = Session()

        super().__init__(session=session, definitions=definitions)

    def initialize(self, deep_scan: bool = False):
        """Prepares the session by fetching required tokens and metadata."""
        home_page = self.session.request_html(url=XUrls.BASE, method="GET")
        if not isinstance(home_page, BeautifulSoup):
            return

        # Handle X Migration
        migrator = XMigrationHandler(session=self.session)
        home_page = migrator.run(response=home_page)

        # Dynamic API Definitions Update
        new_definitions = self.updater.run(response=str(home_page), deep_scan=deep_scan)

        # ClientTransaction Bundle
        ondemand_s_bundle_file = self.parser.get_bundle_url(
            bundle_name="ondemand.s", html_content=home_page
        )
        ondemand_file_response = self.session.request_html(
            url=ondemand_s_bundle_file, method="GET"
        )

        self._apply_updates(
            home_page=home_page,
            ondemand_file_response=str(ondemand_file_response),
            new_definitions=new_definitions,
        )

        # guest token (x-guest-token / gt)
        self.session.request(url=XUrls.GUEST_TOKEN, method="POST")

        logger.info("TweeterPy Client initialized successfully.")


class TweeterPyAsync(TweeterPyClient):
    def __init__(
        self,
        session: Optional[TweeterPySession] = None,
        definitions: Optional[APIDefinition] = None,
    ) -> None:
        if session is None:
            session = AsyncSession()

        super().__init__(session, definitions)

    async def initialize(self, deep_scan: bool = False, max_concurrency: int = 10):
        """Prepares the session by fetching required tokens and metadata."""
        home_page = await self.session.request_html(url=XUrls.BASE, method="GET")
        if not isinstance(home_page, BeautifulSoup):
            return

        # Handle X Migration
        migrator = XMigrationHandler(session=self.session)
        home_page = await migrator.run_async(response=home_page)

        # Dynamic API Definitions Update
        new_definitions = await self.updater.run_async(
            response=str(home_page),
            deep_scan=deep_scan,
            max_concurrency=max_concurrency,
        )

        # ClientTransaction Bundle
        ondemand_s_bundle_file = self.parser.get_bundle_url(
            bundle_name="ondemand.s", html_content=home_page
        )
        ondemand_file_response = await self.session.request_html(
            url=ondemand_s_bundle_file, method="GET"
        )

        self._apply_updates(
            home_page=home_page,
            ondemand_file_response=str(ondemand_file_response),
            new_definitions=new_definitions,
        )

        # guest token (x-guest-token / gt)
        await self.session.request(url=XUrls.GUEST_TOKEN, method="POST")

        logger.info("TweeterPy Client initialized successfully.")


if __name__ == "__main__":
    pass
