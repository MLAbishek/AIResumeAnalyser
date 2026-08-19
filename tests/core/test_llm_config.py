"""
Targeted tests for the OpenRouter LLM configuration added to
app/core/config.py. These verify the Settings class in isolation
(bypassing the real .env file) so they don't depend on whatever key
happens to be configured in this environment.
"""

from app.core.config import Settings


def _settings(**overrides) -> Settings:
    return Settings(
        _env_file=None,
        database_url="postgresql://test/test",
        jwt_secret_key="test-secret",
        **overrides,
    )


class TestLLMConfigDefaults:
    def test_llm_explanations_disabled_by_default(self):
        settings = _settings()

        assert settings.enable_llm_explanations is False

    def test_model_default_is_gpt_oss_20b_free(self):
        settings = _settings()

        assert settings.openrouter_model == "openai/gpt-oss-20b:free"

    def test_base_url_default_is_openrouter(self):
        settings = _settings()

        assert (
            settings.openrouter_base_url
            == "https://openrouter.ai/api/v1"
        )

    def test_missing_api_key_defaults_to_empty_string_not_error(
        self,
    ):
        settings = _settings()

        assert settings.openrouter_api_key == ""

    def test_timeout_has_a_positive_default(self):
        settings = _settings()

        assert settings.llm_timeout_seconds > 0


class TestLLMConfigLoadsFromEnvironment:
    def test_api_key_loads_correctly_from_env_var(
        self, monkeypatch
    ):
        monkeypatch.setenv(
            "OPENROUTER_API_KEY", "test-key-abc123"
        )

        settings = _settings()

        assert settings.openrouter_api_key == "test-key-abc123"

    def test_enable_flag_loads_correctly_from_env_var(
        self, monkeypatch
    ):
        monkeypatch.setenv("ENABLE_LLM_EXPLANATIONS", "true")

        settings = _settings()

        assert settings.enable_llm_explanations is True

    def test_model_and_base_url_overridable_from_env(
        self, monkeypatch
    ):
        monkeypatch.setenv(
            "OPENROUTER_MODEL", "some/other-model"
        )
        monkeypatch.setenv(
            "OPENROUTER_BASE_URL",
            "https://example.invalid/v1",
        )

        settings = _settings()

        assert settings.openrouter_model == "some/other-model"
        assert (
            settings.openrouter_base_url
            == "https://example.invalid/v1"
        )
