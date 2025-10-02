"""
Tests for multi-photo AI calorie estimation
Feature: 003-update-logic-for
Task: T013
"""

from unittest.mock import Mock, patch

import pytest


class TestMultiPhotoEstimation:
    """Test AI estimation service with multiple photos"""

    @pytest.mark.asyncio
    async def test_estimate_with_multiple_photos(self):
        """Should send all photos to OpenAI in single API call"""
        photo_urls = [
            "https://storage.example.com/photo1.jpg",
            "https://storage.example.com/photo2.jpg",
            "https://storage.example.com/photo3.jpg",
        ]

        # Mock the module-level OpenAI client before importing CalorieEstimator
        with patch("calorie_track_ai_bot.services.estimator.client") as mock_client:
            # Mock OpenAI response with macronutrients
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = """
            {
                "kcal_min": 580,
                "kcal_max": 720,
                "kcal_mean": 650,
                "macronutrients": {"protein": 45.5, "carbs": 75.0, "fats": 18.2},
                "confidence": 0.85,
                "items": []
            }
            """
            # Use Mock (not AsyncMock) because the OpenAI client is synchronous
            mock_client.chat.completions.create = Mock(return_value=mock_response)

            from calorie_track_ai_bot.services.estimator import CalorieEstimator

            estimator = CalorieEstimator()

            result = await estimator.estimate_from_photos(
                photo_urls=photo_urls, description="Chicken pasta dinner"
            )

            # Verify single API call with all photos
            mock_client.chat.completions.create.assert_called_once()
            call_args = mock_client.chat.completions.create.call_args

            # Check that all photo URLs were included
            messages = call_args.kwargs["messages"]
            assert len(messages) == 1
            content = messages[0]["content"]

            # Should have text + 3 images
            image_contents = [c for c in content if c.get("type") == "image_url"]
            assert len(image_contents) == 3

            # Verify result structure
            assert result["calories"]["estimate"] == 650
            assert result["macronutrients"]["protein"] == 45.5
            assert result["macronutrients"]["carbs"] == 75.0
            assert result["macronutrients"]["fats"] == 18.2
            assert result["confidence"] == 0.85

    @pytest.mark.asyncio
    async def test_extract_macronutrients_from_response(self):
        """Should extract protein, carbs, fats in grams from AI response"""
        from calorie_track_ai_bot.services.estimator import CalorieEstimator

        estimator = CalorieEstimator()

        ai_response = {
            "calories": {"min": 500, "max": 700, "estimate": 600},
            "macronutrients": {"protein": 30.0, "carbs": 80.0, "fats": 15.5},
            "confidence": 0.9,
        }

        macros = estimator.extract_macronutrients(ai_response)

        assert macros["protein"] == 30.0
        assert macros["carbs"] == 80.0
        assert macros["fats"] == 15.5

    @pytest.mark.asyncio
    async def test_estimate_without_text_description(self):
        """Should create estimate from photos only without text"""
        photo_urls = [
            "https://storage.example.com/photo1.jpg",
            "https://storage.example.com/photo2.jpg",
        ]

        # Mock the module-level OpenAI client before importing CalorieEstimator
        with patch("calorie_track_ai_bot.services.estimator.client") as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = """
            {
                "kcal_min": 400,
                "kcal_max": 600,
                "kcal_mean": 500,
                "macronutrients": {"protein": 25.0, "carbs": 60.0, "fats": 12.0},
                "confidence": 0.75,
                "items": []
            }
            """
            # Use Mock (not AsyncMock) because the OpenAI client is synchronous
            mock_client.chat.completions.create = Mock(return_value=mock_response)

            from calorie_track_ai_bot.services.estimator import CalorieEstimator

            estimator = CalorieEstimator()

            # No description provided
            result = await estimator.estimate_from_photos(photo_urls=photo_urls, description=None)

            assert result is not None
            assert result["calories"]["estimate"] == 500
            assert "macronutrients" in result

    @pytest.mark.asyncio
    async def test_photo_count_tracking(self):
        """Should track number of photos used in estimation"""
        # Test with different photo counts
        for count in [1, 2, 3, 4, 5]:
            photo_urls = [f"https://storage.example.com/photo{i}.jpg" for i in range(count)]

            # Mock the module-level OpenAI client before importing CalorieEstimator
            with patch("calorie_track_ai_bot.services.estimator.client") as mock_client:
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = """
                {
                    "kcal_min": 400,
                    "kcal_max": 600,
                    "kcal_mean": 500,
                    "macronutrients": {"protein": 25.0, "carbs": 60.0, "fats": 12.0},
                    "confidence": 0.8,
                    "items": []
                }
                """
                # Use Mock (not AsyncMock) because the OpenAI client is synchronous
                mock_client.chat.completions.create = Mock(return_value=mock_response)

                from calorie_track_ai_bot.services.estimator import CalorieEstimator

                estimator = CalorieEstimator()

                result = await estimator.estimate_from_photos(photo_urls=photo_urls)

                assert result["photo_count"] == count

    @pytest.mark.asyncio
    async def test_partial_photo_upload_handling(self):
        """Should handle case where some photos fail to upload"""
        from calorie_track_ai_bot.services.estimator import CalorieEstimator

        estimator = CalorieEstimator()

        # Mix of valid and None URLs (representing failed uploads)
        photo_urls = [
            "https://storage.example.com/photo1.jpg",
            None,  # Failed upload
            "https://storage.example.com/photo3.jpg",
        ]

        # Should filter out None values and process valid photos
        valid_urls = estimator.filter_valid_photo_urls(photo_urls)

        assert len(valid_urls) == 2
        assert None not in valid_urls
