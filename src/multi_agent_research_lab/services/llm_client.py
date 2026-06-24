"""LLM client abstraction.

Production note: agents should depend on this interface instead of importing an SDK directly.
"""

from dataclasses import dataclass
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from multi_agent_research_lab.core.config import get_settings


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


# Pricing per 1M tokens
MODEL_PRICING = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 5.00, "output": 15.00},
}


class LLMClient:
    """Provider-agnostic LLM client implementation using OpenAI."""

    def __init__(self) -> None:
        self.settings = get_settings()
        if not self.settings.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set. Please add it to your .env file."
            )
        self.client = OpenAI(
            api_key=self.settings.openai_api_key,
            base_url=self.settings.openai_base_url,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion with token usage and cost tracking."""
        model = self.settings.openai_model
        
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            timeout=float(self.settings.timeout_seconds),
        )

        content = response.choices[0].message.content or ""
        usage = response.usage

        if usage:
            input_tokens = usage.prompt_tokens
            output_tokens = usage.completion_tokens
            
            # Calculate cost
            pricing = MODEL_PRICING.get(model, MODEL_PRICING["gpt-4o-mini"])
            cost_usd = (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000
        else:
            input_tokens = None
            output_tokens = None
            cost_usd = None

        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
        )

