import logging
import time
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are an explanation generator for an AI resume screening system.

You are NOT the decision maker. You must explain the supplied evaluation results.

Rules:
1. Use only the supplied candidate, job, ranking, decision, gap, and evidence information.
2. Never invent qualifications, experience, skills, education, or job requirements.
3. Never change the supplied score.
4. Never change the supplied eligibility result.
5. Never change the supplied decision.
6. Never claim that a candidate has experience unless it appears in the supplied data.
7. Clearly distinguish strengths from gaps.
8. If evidence is insufficient, say so.
9. Do not make hiring decisions independently.
10. Do not produce discriminatory or irrelevant personal inferences.
11. Do not mention internal chain-of-thought or hidden reasoning.
12. Produce only the final explanation text intended for the application UI: \
a short recruiter-facing paragraph of 3-5 sentences. No markdown, no headers, no JSON."""


class LLMExplanationService:
    """
    Thin isolation layer around the OpenRouter (OpenAI-compatible)
    chat completions API. Nothing else in the application calls
    OpenRouter directly - callers only ever use
    generate_explanation().

    This is strictly an enhancement layer: it turns an already-
    computed deterministic evaluation into a natural-language
    explanation. It never computes scores, eligibility, or
    decisions, and it never raises - a disabled/misconfigured/failed
    request always returns None so the caller can fall back to the
    existing deterministic explanation.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        enabled: bool | None = None,
    ):
        self.api_key = (
            api_key
            if api_key is not None
            else settings.openrouter_api_key
        )
        self.model = model or settings.openrouter_model
        self.base_url = (
            base_url or settings.openrouter_base_url
        ).rstrip("/")
        self.timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else settings.llm_timeout_seconds
        )
        self.enabled = (
            enabled
            if enabled is not None
            else settings.enable_llm_explanations
        )

    def generate_explanation(
        self,
        context: dict[str, Any],
    ) -> str | None:
        """
        Generate a grounded, recruiter-facing explanation paragraph
        from an already-computed deterministic evaluation context.

        Returns None (never raises) if the LLM is disabled, not
        configured, or the request fails for any reason - the caller
        is responsible for falling back to its own deterministic
        explanation text in that case.
        """

        if not self.enabled:
            logger.debug(
                "LLM explanation skipped: disabled by configuration."
            )
            return None

        if not self.api_key:
            logger.debug(
                "LLM explanation skipped: no API key configured."
            )
            return None

        user_prompt = self._build_user_prompt(context)
        start = time.monotonic()

        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT,
                        },
                        {
                            "role": "user",
                            "content": user_prompt,
                        },
                    ],
                    "temperature": 0.2,
                    "max_tokens": 400,
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            body = response.json()

            choices = body.get("choices") or []
            text = None

            if choices:
                text = (
                    choices[0]
                    .get("message", {})
                    .get("content")
                )

            latency = time.monotonic() - start

            if not text or not text.strip():
                logger.warning(
                    "LLM explanation returned empty content. "
                    "model=%s latency=%.2fs",
                    self.model,
                    latency,
                )
                return None

            logger.info(
                "LLM explanation succeeded. "
                "model=%s latency=%.2fs",
                self.model,
                latency,
            )

            return text.strip()

        except httpx.TimeoutException:
            logger.warning(
                "LLM explanation timed out. "
                "model=%s timeout=%.1fs",
                self.model,
                self.timeout_seconds,
            )
            return None
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "LLM explanation failed with HTTP %s. model=%s",
                exc.response.status_code,
                self.model,
            )
            return None
        except Exception as exc:
            logger.warning(
                "LLM explanation failed unexpectedly. "
                "model=%s error_type=%s",
                self.model,
                type(exc).__name__,
            )
            return None

    def _build_user_prompt(
        self,
        context: dict[str, Any],
    ) -> str:
        """
        Render the supplied structured context (job, candidate,
        evaluation, gaps, evidence - all already computed by the
        deterministic pipeline) into a compact prompt. No raw
        resume/JD text is included; only the already-extracted
        structured facts are sent.
        """

        import json

        return (
            "Explain the following AI resume screening result for "
            "a recruiter. The score, eligibility, and decision are "
            "already final - only explain them, do not recompute "
            "them.\n\n"
            "DATA:\n"
            + json.dumps(context, indent=2, default=str)
        )
