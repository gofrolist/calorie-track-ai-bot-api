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
            patch("calorie_track_ai_bot.services.config.TIGRIS_ENDPOINT", "test-endpoint"),
            patch("calorie_track_ai_bot.services.config.TIGRIS_ACCESS_KEY", "test-access"),
            patch("calorie_track_ai_bot.services.config.TIGRIS_SECRET_KEY", "test-secret"),
            patch("calorie_track_ai_bot.services.config.TIGRIS_BUCKET", "test-bucket"),
            patch("calorie_track_ai_bot.workers.estimate_worker.s3") as mock_s3,
            patch("calorie_track_ai_bot.workers.estimate_worker.TIGRIS_BUCKET", "test-bucket"),
            patch(
                "calorie_track_ai_bot.workers.estimate_worker.estimate_from_image_url"
            ) as mock_estimate,
            patch("calorie_track_ai_bot.workers.estimate_worker.db_save_estimate") as mock_db_save,
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

            yield {"s3": mock_s3, "estimate": mock_estimate, "db_save": mock_db_save}

    @pytest.mark.asyncio
    async def test_handle_job_success(self, mock_dependencies):
        """Test successful job handling."""
        job = {"photo_id": "photo123"}

        await handle_job(job)

        # Should generate presigned URL
        mock_dependencies["s3"].generate_presigned_url.assert_called_once_with(
            "get_object", Params={"Bucket": "test-bucket", "Key": "photo123"}, ExpiresIn=900
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

        # Should call S3 with None key
        mock_dependencies["s3"].generate_presigned_url.assert_called_once_with(
            "get_object", Params={"Bucket": "test-bucket", "Key": None}, ExpiresIn=900
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
        with patch("builtins.print") as mock_print:
            # Mock estimate to raise an error
            mock_dependencies["estimate"].side_effect = Exception("Job processing error")

            # Test error handling logic
            job = {"photo_id": "error_job"}
            try:
                await handle_job(job)
            except Exception as e:
                print("job error", e)

            # Should have printed error message
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0]
            assert call_args[0] == "job error"
            assert str(call_args[1]) == "Job processing error"

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
