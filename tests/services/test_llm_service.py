"""
Targeted unit tests for the OpenRouter LLM explanation service
(app/services/llm_service.py). All network calls are mocked here -
no live API key is used in these tests. The one live call against
the real OpenRouter API lives in
tests/services/test_llm_service_live_smoke.py and is not part of
this file.
"""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.services.llm_service import (
    SYSTEM_PROMPT,
    LLMExplanationService,
)


SAMPLE_CONTEXT = {
    "job": {
        "title": "Python Developer",
        "required_skills": ["Python", "Docker"],
        "preferred_skills": [],
        "responsibilities": [],
    },
    "candidate": {
        "skills": ["Python"],
        "experience": [
            {"role": "Backend Engineer", "company": "Acme"}
        ],
        "education": [],
    },
    "evaluation": {
        "eligible": True,
        "final_score_percent": 65.57,
        "decision": "review",
        "decision_reason": "Meets most requirements.",
        "ranking_components": {
            "skill_score": 1.0,
            "experience_score": 1.0,
            "semantic_score": 0.0286,
        },
    },
    "gaps": {
        "missing_skills": ["Docker"],
        "experience_gap": {"has_gap": False},
        "education_gap": {"has_gap": False},
        "certification_gap": {"has_gap": False},
    },
    "evidence": [
        {"claim": "Candidate has Python.", "evidence": "Python"}
    ],
}


def _fake_success_response(content: str = "Grounded explanation."):
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {
        "choices": [
            {"message": {"content": content}},
        ]
    }
    return response


class TestConfiguration:
    def test_disabled_by_default_setting_skips_without_network_call(
        self,
    ):
        service = LLMExplanationService(
            api_key="fake-key",
            enabled=False,
        )

        with patch("app.services.llm_service.httpx.post") as post:
            result = service.generate_explanation(SAMPLE_CONTEXT)

        assert result is None
        post.assert_not_called()

    def test_missing_api_key_is_handled_safely_without_network_call(
        self,
    ):
        service = LLMExplanationService(
            api_key="",
            enabled=True,
        )

        with patch("app.services.llm_service.httpx.post") as post:
            result = service.generate_explanation(SAMPLE_CONTEXT)

        assert result is None
        post.assert_not_called()

    def test_model_and_base_url_defaults_match_openrouter_spec(self):
        service = LLMExplanationService(
            api_key="fake-key",
            enabled=True,
        )

        assert service.model == "openai/gpt-oss-20b:free"
        assert service.base_url == "https://openrouter.ai/api/v1"

    def test_explicit_overrides_take_precedence_over_settings(self):
        service = LLMExplanationService(
            api_key="explicit-key",
            model="some/other-model",
            base_url="https://example.invalid/v1",
            timeout_seconds=5.0,
            enabled=True,
        )

        assert service.api_key == "explicit-key"
        assert service.model == "some/other-model"
        assert service.base_url == "https://example.invalid/v1"
        assert service.timeout_seconds == 5.0

    def test_api_key_never_appears_in_repr(self):
        service = LLMExplanationService(
            api_key="super-secret-key-value",
            enabled=True,
        )

        assert "super-secret-key-value" not in repr(service)
        assert "super-secret-key-value" not in str(
            service.__dict__.keys()
        )


class TestSuccessfulCall:
    def test_sends_correct_model_url_and_auth_header(self):
        service = LLMExplanationService(
            api_key="fake-key",
            model="openai/gpt-oss-20b:free",
            base_url="https://openrouter.ai/api/v1",
            enabled=True,
        )

        with patch(
            "app.services.llm_service.httpx.post",
            return_value=_fake_success_response(),
        ) as post:
            result = service.generate_explanation(SAMPLE_CONTEXT)

        assert result == "Grounded explanation."

        args, kwargs = post.call_args
        assert args[0] == "https://openrouter.ai/api/v1/chat/completions"
        assert (
            kwargs["headers"]["Authorization"] == "Bearer fake-key"
        )
        assert kwargs["json"]["model"] == "openai/gpt-oss-20b:free"

    def test_prompt_includes_system_rules_and_grounded_context(self):
        service = LLMExplanationService(
            api_key="fake-key",
            enabled=True,
        )

        with patch(
            "app.services.llm_service.httpx.post",
            return_value=_fake_success_response(),
        ) as post:
            service.generate_explanation(SAMPLE_CONTEXT)

        _, kwargs = post.call_args
        messages = kwargs["json"]["messages"]

        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == SYSTEM_PROMPT
        assert "Never invent qualifications" in SYSTEM_PROMPT
        assert "Never change the supplied score" in SYSTEM_PROMPT

        user_content = messages[1]["content"]
        # The grounded facts already computed by the deterministic
        # pipeline are present in the prompt sent to the model.
        assert "Python Developer" in user_content
        assert "65.57" in user_content
        assert "review" in user_content
        assert "Docker" in user_content

    def test_response_extraction_strips_whitespace(self):
        service = LLMExplanationService(
            api_key="fake-key",
            enabled=True,
        )

        with patch(
            "app.services.llm_service.httpx.post",
            return_value=_fake_success_response(
                "  Explanation with padding.  \n"
            ),
        ):
            result = service.generate_explanation(SAMPLE_CONTEXT)

        assert result == "Explanation with padding."


class TestFailureHandling:
    def test_timeout_returns_none_without_raising(self):
        service = LLMExplanationService(
            api_key="fake-key",
            enabled=True,
        )

        with patch(
            "app.services.llm_service.httpx.post",
            side_effect=httpx.TimeoutException("timed out"),
        ):
            result = service.generate_explanation(SAMPLE_CONTEXT)

        assert result is None

    def test_http_error_returns_none_without_raising(self):
        service = LLMExplanationService(
            api_key="fake-key",
            enabled=True,
        )

        fake_response = MagicMock()
        fake_response.status_code = 401

        with patch(
            "app.services.llm_service.httpx.post",
            side_effect=httpx.HTTPStatusError(
                "unauthorized",
                request=MagicMock(),
                response=fake_response,
            ),
        ):
            result = service.generate_explanation(SAMPLE_CONTEXT)

        assert result is None

    def test_malformed_response_returns_none(self):
        service = LLMExplanationService(
            api_key="fake-key",
            enabled=True,
        )

        bad_response = MagicMock()
        bad_response.raise_for_status = MagicMock()
        bad_response.json.return_value = {"unexpected": "shape"}

        with patch(
            "app.services.llm_service.httpx.post",
            return_value=bad_response,
        ):
            result = service.generate_explanation(SAMPLE_CONTEXT)

        assert result is None

    def test_empty_content_returns_none(self):
        service = LLMExplanationService(
            api_key="fake-key",
            enabled=True,
        )

        with patch(
            "app.services.llm_service.httpx.post",
            return_value=_fake_success_response(""),
        ):
            result = service.generate_explanation(SAMPLE_CONTEXT)

        assert result is None

    def test_unexpected_exception_returns_none(self):
        service = LLMExplanationService(
            api_key="fake-key",
            enabled=True,
        )

        with patch(
            "app.services.llm_service.httpx.post",
            side_effect=ValueError("boom"),
        ):
            result = service.generate_explanation(SAMPLE_CONTEXT)

        assert result is None

    def test_api_key_never_logged_on_failure(self, caplog):
        service = LLMExplanationService(
            api_key="super-secret-key-value",
            enabled=True,
        )

        with patch(
            "app.services.llm_service.httpx.post",
            side_effect=httpx.TimeoutException("timed out"),
        ):
            with caplog.at_level("DEBUG"):
                service.generate_explanation(SAMPLE_CONTEXT)

        for record in caplog.records:
            assert "super-secret-key-value" not in record.getMessage()
