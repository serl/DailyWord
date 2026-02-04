import json
from unittest.mock import MagicMock, patch

import pytest

from dailyword.services.openrouter import (
    OpenRouterError,
    OpenRouterService,
    WordDefinition,
)


class TestOpenRouterServiceInit:
    def test_init_from_settings(self, settings):
        settings.OPENROUTER_API_KEY = "settings-key"
        service = OpenRouterService()
        assert service.api_key == "settings-key"

    def test_init_no_api_key_raises_error(self, settings):
        settings.OPENROUTER_API_KEY = ""
        with pytest.raises(OpenRouterError) as exc_info:
            OpenRouterService()
        assert "API key not configured" in str(exc_info.value)


class TestOpenRouterServiceMakeRequest:
    @pytest.fixture
    def service(self, settings):
        settings.OPENROUTER_API_KEY = "test-key"
        return OpenRouterService()

    def test_make_request_success(self, service):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}

        with patch("dailyword.services.openrouter.requests.post") as mock_post:
            mock_post.return_value = mock_response
            result = service._make_request({"test": "data"})

        assert result == {"result": "success"}
        mock_post.assert_called_once_with(
            service.BASE_URL,
            json={"test": "data"},
            headers={
                "Authorization": "Bearer test-key",
                "Content-Type": "application/json",
            },
        )

    def test_make_request_error(self, service):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = '{"error": "bad request"}'

        with patch("dailyword.services.openrouter.requests.post") as mock_post:
            mock_post.return_value = mock_response
            with pytest.raises(OpenRouterError) as exc_info:
                service._make_request({"test": "data"})

        assert "400" in str(exc_info.value)


class TestGenerateWordList:
    @pytest.fixture
    def service(self, settings):
        settings.OPENROUTER_API_KEY = "test-key"
        settings.OPENROUTER_TEXT_MODEL = "test/model"
        return OpenRouterService()

    def test_generate_word_list_success(self, service):
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "words": [
                                    {
                                        "word": "word1",
                                        "definition": "definition 1",
                                        "example_sentence": "example 1",
                                        "pronunciation": "pron 1",
                                        "part_of_speech": "noun",
                                    },
                                    {
                                        "word": "word2",
                                        "definition": "definition 2",
                                        "example_sentence": "example 2",
                                        "pronunciation": "pron 2",
                                        "part_of_speech": "verb",
                                    },
                                ]
                            }
                        )
                    }
                }
            ]
        }

        with patch.object(service, "_make_request", return_value=mock_response):
            result = service.generate_word_list("technology", count=2)

        assert len(result) == 2
        assert all(isinstance(w, WordDefinition) for w in result)
        assert result[0].word == "word1"
        assert result[1].word == "word2"

    def test_generate_word_list_with_params(self, service):
        mock_response = {
            "choices": [{"message": {"content": json.dumps({"words": []})}}]
        }

        with patch.object(
            service, "_make_request", return_value=mock_response
        ) as mock_req:
            service.generate_word_list("cooking", count=5, difficulty="advanced")

        call_args = mock_req.call_args[0][0]
        content = call_args["messages"][0]["content"]
        assert "5" in content
        assert "cooking" in content
        assert "advanced" in content

    def test_generate_word_list_empty_result(self, service):
        mock_response = {"choices": [{"message": {"content": json.dumps({})}}]}

        with patch.object(service, "_make_request", return_value=mock_response):
            result = service.generate_word_list("test")

        assert result == []

    def test_generate_word_list_missing_optional_fields(self, service):
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "words": [
                                    {
                                        "word": "test",
                                        "definition": "a test definition",
                                    }
                                ]
                            }
                        )
                    }
                }
            ]
        }

        with patch.object(service, "_make_request", return_value=mock_response):
            result = service.generate_word_list("test")

        assert len(result) == 1
        assert result[0].word == "test"
        assert result[0].example_sentence == ""
        assert result[0].pronunciation == ""
        assert result[0].part_of_speech == ""

    def test_generate_word_list_invalid_json(self, service):
        mock_response = {"choices": [{"message": {"content": "not json"}}]}

        with (
            patch.object(service, "_make_request", return_value=mock_response),
            pytest.raises(OpenRouterError),
        ):
            service.generate_word_list("test")

    def test_generate_word_list_missing_key(self, service):
        mock_response = {"wrong": "structure"}

        with (
            patch.object(service, "_make_request", return_value=mock_response),
            pytest.raises(OpenRouterError, match="Failed to parse"),
        ):
            service.generate_word_list("test")


class TestServiceSettings:
    def test_custom_text_model(self, settings):
        settings.OPENROUTER_API_KEY = "test-key"
        settings.OPENROUTER_TEXT_MODEL = "custom/model"

        service = OpenRouterService()

        mock_response = {
            "choices": [{"message": {"content": json.dumps({"words": []})}}]
        }

        with patch.object(
            service, "_make_request", return_value=mock_response
        ) as mock_req:
            service.generate_word_list("test")

        call_args = mock_req.call_args[0][0]
        assert call_args["model"] == "custom/model"
