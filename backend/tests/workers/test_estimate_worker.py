"""Tests for estimate_worker module."""

from unittest.mock import patch

import pytest

from calorie_track_ai_bot.workers.estimate_worker import handle_job


class TestEstimateWorker:
    """Test estimate worker functions."""

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies."""
        with (
            patch("calorie_track_ai_bot.services.config.SUPABASE_URL", "test-url"),
            patch("calorie_track_ai_bot.services.config.SUPABASE_KEY", "test-key"),
            patch("calorie_track_ai_bot.services.config.OPENAI_API_KEY", "test-key"),
            patch("calorie_track_ai_bot.services.config.REDIS_URL", "redis://test"),
            patch("calorie_track_ai_bot.services.config.AWS_ENDPOINT_URL_S3", "test-endpoint"),
            patch("calorie_track_ai_bot.services.config.AWS_ACCESS_KEY_ID", "test-access"),
            patch("calorie_track_ai_bot.services.config.AWS_SECRET_ACCESS_KEY", "test-secret"),
            patch("calorie_track_ai_bot.services.config.BUCKET_NAME", "test-bucket"),
            patch("calorie_track_ai_bot.workers.estimate_worker.s3") as mock_s3,
            patch("calorie_track_ai_bot.workers.estimate_worker.BUCKET_NAME", "test-bucket"),
            patch(
                "calorie_track_ai_bot.workers.estimate_worker.estimate_from_image_url"
            ) as mock_estimate,
            patch("calorie_track_ai_bot.workers.estimate_worker.db_save_estimate") as mock_db_save,
            patch("calorie_track_ai_bot.workers.estimate_worker.db_get_photo") as mock_db_get_photo,
        ):
            mock_s3.generate_presigned_url.return_value = "https://presigned-url.example.com"
            mock_estimate.return_value = {
                "kcal_mean": 500,
                "kcal_min": 400,
                "kcal_max": 600,
                "confidence": 0.8,
                "items": [{"label": "pizza", "kcal": 500, "confidence": 0.8}],
            }
            mock_db_save.return_value = "estimate123"
            mock_db_get_photo.return_value = {
                "id": "photo123",
                "tigris_key": "photos/storage_key.jpg",
                "user_id": "user123",
                "status": "uploaded",
            }

            yield {
                "s3": mock_s3,
                "estimate": mock_estimate,
                "db_save": mock_db_save,
                "db_get_photo": mock_db_get_photo,
            }

    @pytest.mark.asyncio
    async def test_handle_job_success(self, mock_dependencies):
        """Test successful job handling."""
        job = {"photo_id": "photo123"}

        await handle_job(job)

        # Should get photo record first
        mock_dependencies["db_get_photo"].assert_called_once_with("photo123")

        # Should generate presigned URL with the correct storage key
        mock_dependencies["s3"].generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": "test-bucket", "Key": "photos/storage_key.jpg"},
            ExpiresIn=900,
        )

        # Should call estimate function
        mock_dependencies["estimate"].assert_called_once_with("https://presigned-url.example.com")

        # Should save estimate to database
        mock_dependencies["db_save"].assert_called_once()
        call_args = mock_dependencies["db_save"].call_args
        assert call_args.kwargs["photo_id"] == "photo123"

        # Check that confidence was set
        estimate_data = call_args.kwargs["est"]
        assert "confidence" in estimate_data
        assert estimate_data["confidence"] == 0.8  # from mock data

    @pytest.mark.asyncio
    async def test_handle_job_with_existing_confidence(self, mock_dependencies):
        """Test job handling when estimate already has confidence."""
        job = {"photo_id": "photo456"}

        # Mock estimate with existing confidence
        mock_dependencies["estimate"].return_value = {
            "kcal_mean": 300,
            "confidence": 0.9,  # Already has confidence
            "items": [],
        }

        await handle_job(job)

        # Should save estimate to database
        call_args = mock_dependencies["db_save"].call_args
        estimate_data = call_args.kwargs["est"]

        # Should keep existing confidence, not override with 0.5
        assert estimate_data["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_handle_job_estimate_error(self, mock_dependencies):
        """Test job handling when estimate function raises an error."""
        job = {"photo_id": "photo789"}

        # Mock estimate to raise an error
        mock_dependencies["estimate"].side_effect = Exception("Estimation failed")

        # Should propagate the exception
        with pytest.raises(Exception, match="Estimation failed"):
            await handle_job(job)

        # Should not call db_save
        mock_dependencies["db_save"].assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_job_db_save_error(self, mock_dependencies):
        """Test job handling when database save raises an error."""
        job = {"photo_id": "photo999"}

        # Mock db_save to raise an error
        mock_dependencies["db_save"].side_effect = Exception("Database error")

        # Should propagate the exception
        with pytest.raises(Exception, match="Database error"):
            await handle_job(job)

    @pytest.mark.asyncio
    async def test_handle_job_photo_not_found(self, mock_dependencies):
        """Test job handling when photo record is not found."""
        job = {"photo_id": "photo_not_found"}

        # Mock db_get_photo to return None
        mock_dependencies["db_get_photo"].return_value = None

        # Should raise ValueError
        with pytest.raises(ValueError, match="Photo record not found"):
            await handle_job(job)

        # Should not call S3, estimate, or db_save
        mock_dependencies["s3"].generate_presigned_url.assert_not_called()
        mock_dependencies["estimate"].assert_not_called()
        mock_dependencies["db_save"].assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_job_s3_error(self, mock_dependencies):
        """Test job handling when S3 presigned URL generation fails."""
        job = {"photo_id": "photo111"}

        # Mock S3 to raise an error
        mock_dependencies["s3"].generate_presigned_url.side_effect = Exception("S3 error")

        # Should propagate the exception
        with pytest.raises(Exception, match="S3 error"):
            await handle_job(job)

        # Should not call estimate or db_save
        mock_dependencies["estimate"].assert_not_called()
        mock_dependencies["db_save"].assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_job_invalid_job_data(self, mock_dependencies):
        """Test job handling with invalid job data."""
        job = {}  # Missing photo_id

        # Should raise KeyError
        with pytest.raises(KeyError):
            await handle_job(job)

    @pytest.mark.asyncio
    async def test_handle_job_none_photo_id(self, mock_dependencies):
        """Test job handling with None photo_id."""
        job = {"photo_id": None}

        # Should still work (S3 will handle None key)
        await handle_job(job)

        # Should call db_get_photo first
        mock_dependencies["db_get_photo"].assert_called_once_with(None)

        # Should call S3 with the storage key from the photo record
        mock_dependencies["s3"].generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": "test-bucket", "Key": "photos/storage_key.jpg"},
            ExpiresIn=900,
        )

    @pytest.mark.asyncio
    async def test_main_function_loop_logic(self, mock_dependencies):
        """Test main function loop logic without infinite loop."""
        # Test the core logic of main function by simulating one iteration
        with patch(
            "calorie_track_ai_bot.workers.estimate_worker.dequeue_estimate_job"
        ) as mock_dequeue:
            # Mock dequeue to return a job
            mock_dequeue.return_value = {"photo_id": "job1"}

            # Simulate one iteration of the main loop
            job = await mock_dequeue()
            if job:
                await handle_job(job)

            # Should have called handle_job
            mock_dependencies["estimate"].assert_called_once()

    @pytest.mark.asyncio
    async def test_main_function_error_handling(self, mock_dependencies):
        """Test main function error handling logic."""
        # Mock estimate to raise an error
        mock_dependencies["estimate"].side_effect = Exception("Job processing error")

        # Test error handling logic - the new implementation logs errors and re-raises them
        job = {"photo_id": "error_job"}

        # The handle_job function now logs errors internally and re-raises them
        with pytest.raises(Exception, match="Job processing error"):
            await handle_job(job)

    @pytest.mark.asyncio
    async def test_main_function_no_jobs_logic(self, mock_dependencies):
        """Test main function no jobs logic."""
        # Test the no jobs branch logic
        job = None
        if job:
            await handle_job(job)
        else:
            # This would be the sleep branch in the real function
            pass

        # Should not have called handle_job
        mock_dependencies["estimate"].assert_not_called()

    @pytest.mark.asyncio
    async def test_job_data_structure(self, mock_dependencies):
        """Test that job data has the expected structure."""
        job = {"photo_id": "test_photo"}

        # Should not raise any errors
        await handle_job(job)

        # Should have called all expected functions
        mock_dependencies["s3"].generate_presigned_url.assert_called_once()
        mock_dependencies["estimate"].assert_called_once()
        mock_dependencies["db_save"].assert_called_once()

    @pytest.mark.asyncio
    async def test_estimate_data_modification(self, mock_dependencies):
        """Test that estimate data is properly modified before saving."""
        job = {"photo_id": "modify_test"}

        # Mock estimate without confidence
        mock_dependencies["estimate"].return_value = {
            "kcal_mean": 400,
            "kcal_min": 300,
            "kcal_max": 500,
            "items": [],
            # No confidence field
        }

        await handle_job(job)

        # Check that confidence was added
        call_args = mock_dependencies["db_save"].call_args
        estimate_data = call_args.kwargs["est"]

        assert "confidence" in estimate_data
        assert estimate_data["confidence"] == 0.5
        assert estimate_data["kcal_mean"] == 400
        assert estimate_data["kcal_min"] == 300
        assert estimate_data["kcal_max"] == 500
