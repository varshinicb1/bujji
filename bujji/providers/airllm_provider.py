"""BUJJI provider for AirLLM — run massive models on tiny GPU.

Uses AirLLM's AutoModel to load models layer-by-layer, enabling
inference of models like Qwen3-32B, Qwen3-235B, and DeepSeek-V3
on GPUs with as little as 6GB VRAM.

Requires: Python 3.12+, PyTorch with CUDA, airllm >= 3.0
Install: py -3.12 -m pip install airllm
"""

import logging
import sys
from typing import Any, Optional

from bujji.core.models import Message, ProviderResponse
from bujji.providers.base import LLMProvider


class AirLLMProvider(LLMProvider):
    """Provider that uses AirLLM's AutoModel for layer-by-layer inference.

    Supports virtually any HuggingFace model. The model is loaded one
    layer at a time, so total VRAM usage depends on layer size, not
    model size. E.g. Qwen3-235B-A22B runs in ~3GB.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self._model = None
        self._tokenizer = None
        super().__init__(config)

    def _validate_config(self) -> None:
        if "model" not in self.config:
            self.config["model"] = "Qwen/Qwen3-32B"

    @property
    def provider_name(self) -> str:
        return "airllm"

    @property
    def model_name(self) -> str:
        return self.config.get("model", "Qwen/Qwen3-32B")

    def _load_model(self) -> None:
        if self._model is not None:
            return
        try:
            from airllm import AutoModel
        except ImportError:
            raise ImportError(
                "AirLLM is not installed. "
                "Run: py -3.12 -m pip install airllm"
            )
        model_name = self.config["model"]
        compression = self.config.get("compression")
        kwargs = {}
        if compression in ("4bit", "8bit"):
            kwargs["compression"] = compression
        logging.info(f"Loading AirLLM model: {model_name}")
        self._model = AutoModel.from_pretrained(model_name, **kwargs)
        self._tokenizer = self._model.tokenizer

    async def generate(
        self,
        messages: list[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> ProviderResponse:
        self._load_model()

        prompt = self._format_messages(messages)
        max_new = max_tokens or self.config.get("max_tokens", 512)
        temp = temperature if temperature is not None else self.config.get("temperature", 0.1)

        import torch
        inputs = self._tokenizer(
            prompt,
            return_tensors="pt",
            return_attention_mask=False,
            truncation=True,
            max_length=4096,
            padding=False,
        )

        gen_kwargs = dict(
            max_new_tokens=max_new,
            use_cache=True,
            return_dict_in_generate=True,
            do_sample=temp > 0,
            temperature=temp if temp > 0 else None,
        )

        from airllm import AirLLMLlama2
        if isinstance(self._model, AirLLMLlama2):
            generation_output = self._model.generate(
                inputs["input_ids"].cuda(),
                **gen_kwargs,
            )
        else:
            generation_output = self._model.generate(
                inputs["input_ids"].cuda(),
                **gen_kwargs,
            )

        output_text = self._tokenizer.decode(
            generation_output.sequences[0],
            skip_special_tokens=True,
        )

        return ProviderResponse(
            content=output_text,
            model=self.model_name,
            provider=self.provider_name,
            finish_reason="stop",
        )

    async def generate_with_tools(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> ProviderResponse:
        return await self.generate(messages, temperature, max_tokens)

    def _format_messages(self, messages: list[Message]) -> str:
        parts = []
        for msg in messages:
            if msg.role == "system":
                parts.append(f"<|system|>\n{msg.content}</s>")
            elif msg.role == "user":
                parts.append(f"<|user|>\n{msg.content}</s>")
            elif msg.role == "assistant":
                parts.append(f"<|assistant|>\n{msg.content}</s>")
            elif msg.role == "tool":
                parts.append(f"<|tool|>\n{msg.content}</s>")
        parts.append("<|assistant|>\n")
        return "\n".join(parts)
