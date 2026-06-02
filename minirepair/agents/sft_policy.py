"""SFTPolicy: loads a base model with a LoRA adapter for inference."""

from __future__ import annotations

import logging
from pathlib import Path

from minirepair.agents.react_agent import Policy

logger = logging.getLogger(__name__)


class SFTPolicy(Policy):
    """Policy that loads a LoRA adapter on top of a base model."""

    def __init__(
        self,
        base_model_name: str = "Qwen/Qwen2.5-Coder-1.5B-Instruct",
        adapter_path: str | Path = "outputs/sft_adapter",
        max_new_tokens: int = 512,
        temperature: float = 0.0,
        do_sample: bool = False,
        device: str | None = None,
    ) -> None:
        self._base_model_name = base_model_name
        self._adapter_path = Path(adapter_path)
        self._max_new_tokens = max_new_tokens
        self._temperature = temperature
        self._do_sample = do_sample
        self._device = device
        self._model = None
        self._tokenizer = None

    def _load_model(self) -> None:
        if self._model is not None:
            return

        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer

        from minirepair.training.train_sft import resolve_model_path

        model_path = resolve_model_path(self._base_model_name)
        logger.info("Loading base model from: %s", model_path)
        tokenizer = AutoTokenizer.from_pretrained(
            model_path, trust_remote_code=True
        )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        device = self._device or ("cuda" if torch.cuda.is_available() else "cpu")
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map="auto" if device == "cuda" else None,
            trust_remote_code=True,
        )
        if device == "cpu":
            model = model.to(device)

        logger.info("Loading LoRA adapter from %s", self._adapter_path)
        model = PeftModel.from_pretrained(model, str(self._adapter_path))
        model.eval()

        self._model = model
        self._tokenizer = tokenizer
        logger.info("SFTPolicy loaded on %s", device)

    def generate(self, prompt: str) -> str:
        self._load_model()
        assert self._model is not None and self._tokenizer is not None

        import torch

        messages = [{"role": "user", "content": prompt}]
        text = self._tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self._tokenizer(text, return_tensors="pt")
        input_ids = inputs["input_ids"].to(self._model.device)
        attention_mask = inputs["attention_mask"].to(self._model.device)

        with torch.no_grad():
            output_ids = self._model.generate(
                input_ids,
                attention_mask=attention_mask,
                max_new_tokens=self._max_new_tokens,
                do_sample=self._do_sample,
                temperature=self._temperature if self._do_sample else None,
                top_p=0.95 if self._do_sample else None,
            )

        new_tokens = output_ids[0, input_ids.shape[1]:]
        raw_output = self._tokenizer.decode(new_tokens, skip_special_tokens=True)
        return raw_output

    @property
    def policy_type(self) -> str:
        return "sft_qwen_lora"
