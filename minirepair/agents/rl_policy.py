"""RLPolicy: extends SFTPolicy for RL training with LoRA adapter."""

from __future__ import annotations

import logging
from pathlib import Path

from minirepair.agents.sft_policy import SFTPolicy

logger = logging.getLogger(__name__)


class RLPolicy(SFTPolicy):
    """Policy for RL evaluation: loads a LoRA adapter (SFT or RL trained).

    Identical to SFTPolicy in inference behavior. The distinction is
    method_name ("rl_sparse" / "rl_dense") for metrics tracking.
    """

    def __init__(
        self,
        base_model_name: str = "Qwen/Qwen2.5-Coder-1.5B-Instruct",
        adapter_path: str | Path = "outputs/sft_adapter",
        max_new_tokens: int = 512,
        temperature: float = 0.0,
        do_sample: bool = False,
        device: str | None = None,
        policy_type: str = "rl_sparse_qwen_lora",
    ) -> None:
        super().__init__(
            base_model_name=base_model_name,
            adapter_path=adapter_path,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=do_sample,
            device=device,
        )
        self._policy_type = policy_type

    @property
    def policy_type(self) -> str:
        return self._policy_type
