import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from config.settings import (
    YT_CLIENT_ID,
    YT_CLIENT_SECRET,
    YT_REFRESH_TOKEN,
    YT_CATEGORY_ID,
    YT_PRIVACY_STATUS,
    TEST_MODE,
)
from src.utils.logger import logger

RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
MAX_RETRIES = 5

class YouTubeUploader:
    """YouTube Data API v3 uploader for Shorts automation using OAuth2 refresh token."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
        test_mode: Optional[bool] = None,
    ):
        self.client_id = (client_id or YT_CLIENT_ID).strip()
        self.client_secret = (client_secret or YT_CLIENT_SECRET).strip()
        self.refresh_token = (refresh_token or YT_REFRESH_TOKEN).strip()

        if test_mode is None:
            env_test = os.getenv("TEST_MODE", "").strip().lower()
            self.test_mode = env_test in ("true", "1", "yes") if env_test else TEST_MODE
        else:
            self.test_mode = test_mode


    def get_authenticated_service(self):
        """Construct Google API client using OAuth2 refresh token."""
        if not (self.client_id and self.client_secret and self.refresh_token):
            raise ValueError(
                "Missing YouTube OAuth credentials. Ensure YT_CLIENT_ID, "
                "YT_CLIENT_SECRET, and YT_REFRESH_TOKEN are set in environment."
            )

        credentials = Credentials(
            token=None,
            refresh_token=self.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=["https://www.googleapis.com/auth/youtube.upload"],
        )
        return build("youtube", "v3", credentials=credentials)

    def upload_video(
        self,
        video_path: Union[str, Path],
        title: str,
        description: str,
        tags: Optional[List[str]] = None,
        category_id: Optional[str] = None,
        privacy_status: str = "private",
    ) -> Dict[str, Any]:
        """
        Upload video to YouTube channel using resumable chunked upload with backoff retries.
        Skips actual API call when TEST_MODE is active.
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found for upload: {video_path}")

        cat_id = category_id or YT_CATEGORY_ID or "22"
        priv_status = privacy_status or YT_PRIVACY_STATUS or "private"

        clean_tags = [t.strip() for t in (tags or []) if t and t.strip()]

        # Truncate title to 100 chars (YouTube API maximum)
        short_title = title[:100]

        if self.test_mode:
            logger.info("[TEST_MODE] Dry run enabled. Skipping YouTube upload request.")
            logger.info(f" -> Video File: {video_path.resolve()}")
            logger.info(f" -> Title: '{short_title}'")
            logger.info(f" -> Category ID: {cat_id} | Privacy: {priv_status}")
            logger.info(f" -> Tags: {clean_tags}")
            logger.info(f" -> Description Preview:\n{description[:200]}...")

            return {
                "video_id": "DRY_RUN_TEST_ID",
                "url": "https://www.youtube.com/watch?v=DRY_RUN_TEST_ID",
                "status": "SKIPPED_TEST_MODE",
                "title": short_title,
                "privacy_status": priv_status,
            }

        logger.info(f"Starting YouTube video upload for '{short_title}'...")
        youtube = self.get_authenticated_service()

        body = {
            "snippet": {
                "title": short_title,
                "description": description,
                "tags": clean_tags,
                "categoryId": cat_id,
            },
            "status": {
                "privacyStatus": priv_status,
                "selfDeclaredMadeForKids": False,
            },
        }

        # 1MB chunk size for resumable media upload
        media = MediaFileUpload(
            str(video_path),
            mimetype="video/mp4",
            chunksize=1024 * 1024,
            resumable=True,
        )

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = None
        retry_count = 0

        while response is None:
            try:
                logger.debug(f"Uploading chunk for '{video_path.name}'...")
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    logger.info(f" -> Upload progress: {progress}%")
            except HttpError as e:
                if e.resp.status in RETRIABLE_STATUS_CODES:
                    retry_count += 1
                    if retry_count > MAX_RETRIES:
                        logger.error(f"Max retries exceeded for transient error: {e}")
                        raise
                    sleep_secs = 2 ** retry_count
                    logger.warning(
                        f"Transient YouTube API error HTTP {e.resp.status}. "
                        f"Retrying in {sleep_secs}s (Attempt {retry_count}/{MAX_RETRIES})..."
                    )
                    time.sleep(sleep_secs)
                else:
                    logger.error(f"Non-retriable YouTube API HttpError: {e}")
                    raise
            except Exception as exc:
                retry_count += 1
                if retry_count > MAX_RETRIES:
                    logger.error(f"Max retries exceeded for network error: {exc}")
                    raise
                sleep_secs = 2 ** retry_count
                logger.warning(
                    f"Transient network error during upload: {exc}. "
                    f"Retrying in {sleep_secs}s (Attempt {retry_count}/{MAX_RETRIES})..."
                )
                time.sleep(sleep_secs)

        video_id = response.get("id", "")
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        logger.info(f"YouTube upload successful! Video ID: {video_id} | URL: {video_url}")

        return {
            "video_id": video_id,
            "url": video_url,
            "status": "UPLOADED",
            "title": short_title,
            "privacy_status": priv_status,
            "response": response,
        }
