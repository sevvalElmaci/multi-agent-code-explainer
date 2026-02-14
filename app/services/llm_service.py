"""
LLM Service - Ollama (Multi-Agent Compatible)
"""

import logging
import requests
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Ollama LLM'e prompt gönderir ve yanıt döndürür.

        Args:
            prompt: Gönderilecek metin
            model: Override model (örn: llama3.2:1b)
            temperature: Override temperature

        Returns:
            str: LLM yanıtı
        """

        selected_model = model or settings.OLLAMA_MODEL
        selected_temp = temperature or settings.TEMPERATURE

        url = f"{self.base_url}/api/generate"

        payload = {
            "model": selected_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": selected_temp,
                "num_predict": settings.MAX_TOKENS,
            }
        }

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=settings.OLLAMA_TIMEOUT
            )

            response.raise_for_status()
            result = response.json()

            return result.get("response", "")

        except requests.exceptions.RequestException as e:
            logger.error("Ollama LLM çağrısı başarısız", exc_info=True)
            raise RuntimeError("LLM servisi ile iletişim kurulamadı") from e

    # Backward compatibility (eski kod kırılmasın diye)
    def chat(self, message: str) -> str:
        return self.generate(message)
