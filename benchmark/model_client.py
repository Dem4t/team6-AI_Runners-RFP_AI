import time
import logging
from typing import Dict, Any, Optional
from openai import OpenAI, APIError, APIConnectionError

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class ModelClient:
    def __init__(self, name: str, base_url: str, api_key: str, model: str):
        self.name = name
        self.model = model
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        
        self.default_system_prompt = (
            "You are an expert RFP document extraction assistant. "
            "Extract information accurately from the provided RFP text. "
            "Do not invent or assume information. "
            "Return only valid JSON."
        )

    def generate(self, prompt: str, max_tokens: int = 1200, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        start = time.perf_counter()
        active_system_prompt = system_prompt or self.default_system_prompt

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": active_system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=max_tokens,
                response_format={"type": "json_object"}
            )

            end = time.perf_counter()
            usage = response.usage

            return {
                "model": self.name,
                "response": response.choices[0].message.content,
                "latency_seconds": end - start,
                "input_tokens": getattr(usage, "prompt_tokens", 0) if usage else 0,
                "output_tokens": getattr(usage, "completion_tokens", 0) if usage else 0,
                "total_tokens": getattr(usage, "total_tokens", 0) if usage else 0,
                "error": None
            }

        except Exception as e:
            end = time.perf_counter()

            # يوقف البرنامج فوراً لو الحد أو الرصيد خلص
            msg = str(e)
            if "insufficient_quota" in msg or "project_spend_limit_exceeded" in msg:
                raise RuntimeError(
                    "OpenAI quota/spend limit reached; stopping benchmark."
                ) from e

            logger.error(f"API Error during generation with model {self.name}: {str(e)}")

            return {
                "model": self.name,
                "response": None,
                "latency_seconds": end - start,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "error": str(e)
            }