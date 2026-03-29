import random
from typing import Any, Dict, List, Optional, Type, Union

from bs4 import BeautifulSoup
from x_client_transaction import ClientTransaction

from tweeterpy.core.abstractions import TweeterPyLogger
from tweeterpy.core.definition import APIDefinition
from tweeterpy.core.graphql import GraphQLClient
from tweeterpy.core.migration import XMigrationHandler
from tweeterpy.core.resources import XOperations, XUrls
from tweeterpy.core.session import AsyncSession, Session, TweeterPySession
from tweeterpy.log import Logger, StandardLogger
from tweeterpy.schemas.metadata import FeatureSwitch, FieldToggle
from tweeterpy.schemas.operation import Operation
from tweeterpy.services.parser import APIParser
from tweeterpy.services.updater import APIUpdater
from tweeterpy.utils.text import parse_html


class TweeterPyClient:
    def __init__(
        self,
        session: TweeterPySession,
        logger: Optional[Union[TweeterPyLogger, Type[TweeterPyLogger]]] = None,
        definitions: Optional[APIDefinition] = None,
    ) -> None:
        if definitions is None:
            definitions = APIDefinition.from_defaults()

        if logger is None:
            logger = StandardLogger

        self.api_definitions = definitions
        self.graphql_client = GraphQLClient(
            feature_switch=self.api_definitions.feature_switch,
            field_toggle=self.api_definitions.field_toggle,
        )
        self.logger = Logger.get_logger(logger=logger, name=__name__)
        self.parser = APIParser(logger=logger)
        self.session = session
        self.updater = APIUpdater(logger=logger, session=session)
        self._meta_data: Dict[str, Any] = {}

    @property
    def feature_switch(self) -> FeatureSwitch:
        return self.api_definitions.feature_switch

    @property
    def field_toggle(self) -> FieldToggle:
        return self.api_definitions.field_toggle

    @property
    def is_logged_in(self) -> bool:
        has_user = bool(self._meta_data.get("isLoggedIn")) and bool(
            self._meta_data.get("userId")
        )
        has_cookies = all(k in self.session.cookies for k in ("auth_token", "ct0"))
        return has_user and has_cookies

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
        return self.execute(operation=XOperations.Viewer, variables=variables)

    def _apply_updates(
        self,
        home_page: Union[BeautifulSoup, Any],
        ondemand_file_response: str,
        new_definitions: Dict[str, Any],
        session_info: Optional[Dict[str, Any]] = None,
        meta_data: Optional[Dict[str, Any]] = None,
    ):
        """Shared logic to update state from fetched data."""

        # Update API Definitions
        self.api_definitions.feature_switch = FeatureSwitch(
            **new_definitions.get("feature_switch", {})
        )
        self.api_definitions.operations = new_definitions.get("operations", {})
        field_toggle = self.api_definitions.field_toggle
        field_toggle._feature_switch = self.api_definitions.feature_switch
        field_toggle._session = session_info

        # Update GraphQLClient
        self.graphql_client.feature_switch = self.api_definitions.feature_switch
        self.graphql_client.field_toggle = self.api_definitions.field_toggle

        # update metadata
        if isinstance(meta_data, dict):
            self._meta_data.update(meta_data)

        # Initialize ClientTransaction for x-client-transaction-id generation
        try:
            self.session.client_transaction = ClientTransaction(
                home_page_response=parse_html(home_page),
                ondemand_file_response=ondemand_file_response,
            )
        except Exception as error:
            self.logger.warning(f"Could not initialize ClientTransaction: {error}")

    def _get_session_info(self, home_page: BeautifulSoup):
        initial_state = self.parser.parse_initial_state(html_content=home_page)
        if isinstance(initial_state, dict):
            return initial_state.get("session", {})

    def execute(
        self,
        operation: Union[Operation, str],
        variables: Optional[Dict[str, Any]] = None,
    ):
        operation_name = (
            operation.name if isinstance(operation, Operation) else operation
        )
        operation = self.api_definitions.create_operation(operation_name=operation_name)

        request_payload = self.graphql_client.prepare_request(
            operation=operation, variables=variables
        )

        return self.session.request(
            url=f"{XUrls.API_BASE}{request_payload.get('path')}",
            method=request_payload.get("method"),
            headers=request_payload.get("headers"),
            params=request_payload.get("params"),
            json=request_payload.get("json"),
            timeout=request_payload.get("timeout"),
        )

    def profile_spotlights_query(self, username: str):
        variables = {"screen_name": username}
        return self.execute(
            operation=XOperations.ProfileSpotlightsQuery, variables=variables
        )

    def user_by_rest_id(self, user_id: str):
        variables = {"userId": user_id, "withSafetyModeUserFields": True}
        return self.execute(operation=XOperations.UserByRestId, variables=variables)

    def users_by_rest_ids(self, user_ids: List[str]):
        variables = {"userIds": user_ids}
        return self.execute(operation=XOperations.UsersByRestIds, variables=variables)

    def user_by_screen_name(self, screen_name: str):
        variables = {"screen_name": screen_name, "withSafetyModeUserFields": True}
        return self.execute(operation=XOperations.UserByScreenName, variables=variables)

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
        return self.execute(operation=XOperations.UserMedia, variables=variables)

    def user_tweets(self, user_id: str, total: int = 100):
        variables = {
            "userId": user_id,
            "count": total,
            "includePromotedContent": True,
            "withQuickPromoteEligibilityTweetFields": True,
            "withVoice": True,
            "withV2Timeline": True,
        }
        return self.execute(operation=XOperations.UserTweets, variables=variables)

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
            operation=XOperations.UserTweetsAndReplies, variables=variables
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
            operation=XOperations.TweetResultByRestId, variables=variables
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

        return self.execute(operation=XOperations.TweetDetail, variables=variables)

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
        return self.execute(operation=XOperations.Likes, variables=variables)

    def home_timeline(self, total: int = 40):
        variables = {
            "count": total,
            "includePromotedContent": True,
            "latestControlAvailable": True,
            "withCommunity": True,
        }
        return self.execute(operation=XOperations.HomeTimeline, variables=variables)

    def list_latest_tweets_timeline(self, list_id: str, total: int = 100):
        variables = {"listId": list_id, "count": total}
        return self.execute(
            operation=XOperations.ListLatestTweetsTimeline, variables=variables
        )

    def topic_landing_page(self, topic_id: str, total: int = 100):
        variables = {"rest_id": topic_id, "count": total}
        return self.execute(operation=XOperations.TopicLandingPage, variables=variables)

    def followers(self, user_id: str, total: int = 100):
        variables = {"userId": user_id, "count": total, "includePromotedContent": False}
        return self.execute(operation=XOperations.Followers, variables=variables)

    def following(self, user_id: str, total: int = 100):
        variables = {"userId": user_id, "count": total, "includePromotedContent": False}
        return self.execute(operation=XOperations.Following, variables=variables)

    def followers_you_know(self, user_id: str, total: int = 100):
        variables = {"userId": user_id, "count": total, "includePromotedContent": False}
        return self.execute(operation=XOperations.FollowersYouKnow, variables=variables)

    def biz_profile_fetch_user(self, user_id: int):
        variables = {"rest_id": user_id}
        return self.execute(
            operation=XOperations.BizProfileFetchUser, variables=variables
        )

    def favoriters(self, tweet_id: str, total: int = 100):
        variables = {
            "tweetId": tweet_id,
            "count": total,
            "includePromotedContent": True,
        }
        return self.execute(operation=XOperations.Favoriters, variables=variables)

    def retweeters(self, tweet_id: str, total: int = 100):
        variables = {
            "tweetId": tweet_id,
            "count": total,
            "includePromotedContent": True,
        }
        return self.execute(operation=XOperations.Retweeters, variables=variables)

    def user_highlights_tweets(self, user_id: int, total: int = 100):
        variables = {
            "userId": user_id,
            "count": total,
            "includePromotedContent": True,
            "withVoice": True,
        }
        return self.execute(
            operation=XOperations.UserHighlightsTweets, variables=variables
        )

    def search_timeline(self, query: str, search_filter: str = "Top", total: int = 20):
        variables = {
            "rawQuery": query,
            "count": total,
            "querySource": "typed_query",
            "product": search_filter,
        }
        return self.execute(operation=XOperations.SearchTimeline, variables=variables)


class TweeterPy(TweeterPyClient):
    def __init__(
        self,
        logger: Optional[Union[TweeterPyLogger, Type[TweeterPyLogger]]] = None,
        session: Optional[TweeterPySession] = None,
        definitions: Optional[APIDefinition] = None,
    ) -> None:
        if session is None:
            session = Session()

        super().__init__(session=session, definitions=definitions, logger=logger)

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
        session_info = self._get_session_info(home_page=parse_html(home_page))

        # Metadata sync
        meta_data = self.parser.parse_meta_data(html_content=home_page)

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
            session_info=session_info,
            meta_data=meta_data,
        )

        # guest token (x-guest-token / gt)
        self.session.request(url=XUrls.GUEST_TOKEN, method="POST")

        self.logger.info("TweeterPy Client initialized successfully.")

    def login_with_tokens(self, auth_token: str, csrf_token: Optional[str] = None):
        """Authenticates the session using a pre-existing auth_token and ct0 (CSRF token)."""
        tokens = {"auth_token": auth_token}
        if csrf_token:
            tokens.update({"ct0": csrf_token})

        self.session.cookies.update(tokens)
        self.initialize(deep_scan=False)

        if not self.is_logged_in:
            raise Exception("Authentication failed: Tokens are invalid or expired.")

        self.logger.info(f"Successfully logged in as {self._meta_data.get('userId')}")


class TweeterPyAsync(TweeterPyClient):
    def __init__(
        self,
        logger: Optional[Union[TweeterPyLogger, Type[TweeterPyLogger]]] = None,
        session: Optional[TweeterPySession] = None,
        definitions: Optional[APIDefinition] = None,
    ) -> None:
        if session is None:
            session = AsyncSession()

        super().__init__(session=session, definitions=definitions, logger=logger)

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
        session_info = self._get_session_info(home_page=parse_html(home_page))

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
            session_info=session_info,
        )

        # guest token (x-guest-token / gt)
        await self.session.request(url=XUrls.GUEST_TOKEN, method="POST")

        self.logger.info("TweeterPy Client initialized successfully.")

    async def login_with_tokens(
        self, auth_token: str, csrf_token: Optional[str] = None
    ):
        """Authenticates the session using a pre-existing auth_token and ct0 (CSRF token)."""
        tokens = {"auth_token": auth_token}
        if csrf_token:
            tokens.update({"ct0": csrf_token})

        self.session.cookies.update(tokens)
        await self.initialize(deep_scan=False)

        if not self.is_logged_in:
            raise Exception("Authentication failed: Tokens are invalid or expired.")

        self.logger.info(f"Successfully logged in as {self._meta_data.get('userId')}")


if __name__ == "__main__":
    pass
