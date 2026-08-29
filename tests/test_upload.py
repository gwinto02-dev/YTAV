import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from googleapiclient.errors import HttpError
from src.upload.youtube_uploader import YouTubeUploader

def test_uploader_missing_credentials_raises_error():
    uploader = YouTubeUploader(
        client_id="",
        client_secret="",
        refresh_token="",
        test_mode=False
    )
    with pytest.raises(ValueError, match="Missing YouTube OAuth credentials"):
        uploader.get_authenticated_service()

def test_uploader_test_mode_dry_run(tmp_path):
    dummy_video = tmp_path / "test_short.mp4"
    dummy_video.write_bytes(b"dummy video content")

    uploader = YouTubeUploader(
        client_id="",
        client_secret="",
        refresh_token="",
        test_mode=True
    )

    result = uploader.upload_video(
        video_path=dummy_video,
        title="Test Title Beyond One Hundred Characters Long Just To Verify Truncation Handling Works Perfectly As Expected",
        description="Test Description",
        tags=["#test", "shorts"]
    )

    assert result["status"] == "SKIPPED_TEST_MODE"
    assert result["video_id"] == "DRY_RUN_TEST_ID"
    assert result["url"] == "https://www.youtube.com/watch?v=DRY_RUN_TEST_ID"
    assert result["privacy_status"] == "private"
    assert len(result["title"]) <= 100


def test_uploader_file_not_found():
    uploader = YouTubeUploader(test_mode=True)
    with pytest.raises(FileNotFoundError):
        uploader.upload_video(
            video_path=Path("non_existent_file.mp4"),
            title="Title",
            description="Desc"
        )

@patch("src.upload.youtube_uploader.build")
@patch("src.upload.youtube_uploader.Credentials")
@patch("src.upload.youtube_uploader.MediaFileUpload")
def test_uploader_successful_upload(mock_media_file, mock_credentials, mock_build, tmp_path):
    dummy_video = tmp_path / "test_short.mp4"
    dummy_video.write_bytes(b"dummy video content")

    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_insert = MagicMock()
    mock_service.videos().insert.return_value = mock_insert
    mock_insert.next_chunk.return_value = (None, {"id": "YOUTUBE_12345"})

    uploader = YouTubeUploader(
        client_id="dummy_cid",
        client_secret="dummy_csecret",
        refresh_token="dummy_rtoken",
        test_mode=False
    )

    result = uploader.upload_video(
        video_path=dummy_video,
        title="Valid Short Title",
        description="Full Description",
        tags=["facts", "shorts"]
    )

    assert result["status"] == "UPLOADED"
    assert result["video_id"] == "YOUTUBE_12345"
    assert result["url"] == "https://www.youtube.com/watch?v=YOUTUBE_12345"
    assert result["privacy_status"] == "private"

    mock_credentials.assert_called_once()
    mock_service.videos().insert.assert_called_once()

@patch("time.sleep", return_value=None)
@patch("src.upload.youtube_uploader.build")
@patch("src.upload.youtube_uploader.Credentials")
@patch("src.upload.youtube_uploader.MediaFileUpload")
def test_uploader_transient_error_retry(mock_media_file, mock_credentials, mock_build, mock_sleep, tmp_path):
    dummy_video = tmp_path / "test_short.mp4"
    dummy_video.write_bytes(b"dummy video content")

    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_insert = MagicMock()
    mock_service.videos().insert.return_value = mock_insert

    # Simulate 503 error on first call, success on second
    resp_503 = MagicMock(status=503)
    error_503 = HttpError(resp=resp_503, content=b"Service Unavailable")

    status_progress = MagicMock()
    status_progress.progress.return_value = 0.5

    mock_insert.next_chunk.side_effect = [
        error_503,
        (None, {"id": "RETRY_SUCCESS_ID"})
    ]

    uploader = YouTubeUploader(
        client_id="dummy_cid",
        client_secret="dummy_csecret",
        refresh_token="dummy_rtoken",
        test_mode=False
    )

    result = uploader.upload_video(
        video_path=dummy_video,
        title="Retry Test Title",
        description="Desc"
    )

    assert result["status"] == "UPLOADED"
    assert result["video_id"] == "RETRY_SUCCESS_ID"
    assert mock_insert.next_chunk.call_count == 2
    mock_sleep.assert_called_once()
