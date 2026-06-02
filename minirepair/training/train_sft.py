"""LoRA/QLoRA SFT training using TRL SFTTrainer + PEFT."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def resolve_model_path(model_name: str) -> str:
    """Resolve model name to local path, downloading from ModelScope if needed.

    If model_name is a local path that exists, returns it directly.
    Otherwise, tries to download from ModelScope (魔搭社区) and returns the local cache path.
    """
    # If it's a local path that exists, use it directly
    local_path = Path(model_name)
    if local_path.exists():
        return str(local_path.resolve())

    # Try ModelScope download
    try:
        from modelscope import snapshot_download

        logger.info("Downloading model from ModelScope: %s", model_name)
        local_dir = snapshot_download(model_name)
        logger.info("Model downloaded to: %s", local_dir)
        return local_dir
    except ImportError:
        logger.warning("modelscope not installed, falling back to HuggingFace Hub")
        return model_name
    except Exception as e:
        logger.warning("ModelScope download failed (%s), falling back to HuggingFace Hub", e)
        return model_name


def train_sft(config: dict[str, Any], dry_run: bool = False) -> Path:
    """Run SFT training with LoRA.

    Args:
        config: Training configuration dict (from sft.yaml).
        dry_run: If True, only load a few samples and run 1-2 steps.

    Returns:
        Path to the saved adapter directory.
    """
    import datasets
    import peft
    import torch
    import transformers
    import trl

    model_name = config["model_name"]
    dataset_path = config["dataset_path"]
    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    # Resolve model path (download from ModelScope if needed)
    model_path = resolve_model_path(model_name)

    # LoRA config
    lora_config = peft.LoraConfig(
        r=config.get("lora_r", 16),
        lora_alpha=config.get("lora_alpha", 32),
        lora_dropout=config.get("lora_dropout", 0.05),
        target_modules=config.get("target_modules", ["q_proj", "k_proj", "v_proj", "o_proj"]),
        task_type="CAUSAL_LM",
    )

    # Training hyperparameters
    batch_size = config.get("batch_size", 4)
    grad_accum = config.get("gradient_accumulation_steps", 4)
    lr = config.get("learning_rate", 2e-4)
    epochs = config.get("epochs", 3)
    max_seq_length = config.get("max_seq_length", 1024)
    warmup_ratio = config.get("warmup_ratio", 0.1)
    weight_decay = config.get("weight_decay", 0.01)
    logging_steps = config.get("logging_steps", 10)

    # Dry-run overrides
    if dry_run:
        dry_cfg = config.get("dry_run", {})
        max_samples = dry_cfg.get("max_samples", 8)
        max_steps = dry_cfg.get("max_steps", 2)
        epochs = 1
    else:
        max_samples = None
        max_steps = None

    # Load tokenizer and model
    logger.info("Loading model from: %s", model_path)
    tokenizer = transformers.AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = transformers.AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto" if torch.cuda.is_available() else None,
        trust_remote_code=True,
    )

    # Apply LoRA
    model = peft.get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Load dataset
    logger.info("Loading dataset: %s", dataset_path)
    dataset = datasets.load_dataset("json", data_files=str(dataset_path), split="train")
    if max_samples is not None:
        dataset = dataset.select(range(min(max_samples, len(dataset))))

    # Format: messages -> text using tokenizer chat template
    def format_messages(example: dict) -> dict:
        messages = example["messages"]
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        return {"text": text}

    dataset = dataset.map(format_messages, remove_columns=dataset.column_names)

    # Training arguments (use SFTConfig for TRL 1.x)
    training_args = trl.SFTConfig(
        output_dir=str(output_dir),
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=grad_accum,
        learning_rate=lr,
        num_train_epochs=epochs,
        warmup_ratio=warmup_ratio,
        weight_decay=weight_decay,
        logging_steps=logging_steps,
        save_strategy="no",
        fp16=torch.cuda.is_available(),
        report_to="none",
        max_steps=max_steps if dry_run else -1,
        max_length=max_seq_length,
    )

    trainer = trl.SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        processing_class=tokenizer,
    )

    logger.info("Starting SFT training%s", " (dry-run)" if dry_run else "")
    trainer.train()

    # Save adapter
    model.save_pretrained(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))
    logger.info("Adapter saved to %s", output_dir)

    return output_dir
