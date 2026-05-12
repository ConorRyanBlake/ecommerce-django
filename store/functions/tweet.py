"""
Twitter/X API integration for the eCommerce app.

Implemented as a singleton so we authenticate once at app startup
and reuse the same client for every tweet. Falls back to console
logging when no credentials are configured, so the rest of the app
keeps working without X access.
"""

import os
import logging
import tempfile
from urllib.parse import urlparse

import requests
import tweepy
from dotenv import load_dotenv

# Load .env from the project root if it exists
load_dotenv()

logger = logging.getLogger(__name__)


class Tweet:
    """Singleton wrapper around the tweepy client for posting tweets."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            print("Creating the Tweet instance...")
            cls._instance = super().__new__(cls)
            cls._instance.client = None
            cls._instance.api_v1 = None
            cls._instance.authenticated = False
            cls._instance.authenticate()
        return cls._instance

    def authenticate(self):
        """Read credentials from environment and build the tweepy client."""
        api_key = os.getenv("X_API_KEY")
        api_secret = os.getenv("X_API_SECRET")
        access_token = os.getenv("X_ACCESS_TOKEN")
        access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")

        if not all([api_key, api_secret, access_token, access_token_secret]):
            print(
                "Tweet: No X API credentials found in .env - running in fallback mode. "
                "Tweets will be logged to the console instead of being posted."
            )
            return False

        try:
            # v2 client for creating tweets
            self.client = tweepy.Client(
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_token_secret,
            )

            # v1.1 client just for media uploads (v2 doesn't support media yet)
            auth = tweepy.OAuth1UserHandler(
                api_key, api_secret, access_token, access_token_secret
            )
            self.api_v1 = tweepy.API(auth)

            self.authenticated = True
            print("Tweet: X API authentication successful.")
            return True
        except Exception as e:
            print(f"Tweet: Authentication failed - {e}")
            return False

    def make_tweet(self, text, image_url=None):
        """
        Post a tweet. If image_url is provided, downloads and attaches it.
        If posting fails or no credentials exist, logs the tweet to the console.
        """
        # Fallback mode - just log what we would have tweeted
        if not self.authenticated:
            print("=" * 60)
            print("Tweet (fallback mode - not posted to X):")
            print(text)
            if image_url:
                print(f"With image: {image_url}")
            else:
                print("(no image attached)")
            print("=" * 60)
            return False

        media_ids = None

        # Try to upload media if a URL was given
        if image_url:
            try:
                media_ids = [self._upload_media_from_url(image_url)]
            except Exception as e:
                print(f"Tweet: Image upload failed ({e}). Posting text only.")
                media_ids = None

        try:
            response = self.client.create_tweet(text=text, media_ids=media_ids)
            print(f"Tweet posted successfully. ID: {response.data['id']}")
            return True
        except Exception as e:
            print(f"Tweet: Failed to post - {e}")
            # Log what we tried to send for debugging
            print(f"Tweet content was: {text}")
            return False

    def _upload_media_from_url(self, image_url):
        """Download an image from a URL and upload to X. Returns the media_id."""
        # Download the image to a temp file
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()

        # Figure out the file extension from the URL
        parsed = urlparse(image_url)
        ext = os.path.splitext(parsed.path)[1] or ".jpg"

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
            f.write(response.content)
            temp_path = f.name

        try:
            media = self.api_v1.media_upload(temp_path)
            return media.media_id
        finally:
            # Always clean up the temp file
            try:
                os.unlink(temp_path)
            except OSError:
                pass
