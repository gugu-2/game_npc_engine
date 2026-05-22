import os
import sys
import torch
from datasets import load_dataset
from unsloth import FastLanguageModel, is_bfloat16_supported
from unsloth.chat_templates import get_chat_template
from trl import SFTTrainer
from transformers import TrainingArguments

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
MAX_SEQ_LENGTH = 2048
MODEL_NAME = "unsloth/gemma-2-2b-it"
OUTPUT_DIR = "npc_lora_model"
DATA_FILE = "npc_training_data.jsonl"

# Training steps — increase for better quality at cost of more time
# BUG FIX: 60 steps is far too low for a real dataset. Using num_train_epochs
# instead of max_steps ensures we train on ALL the data, not just 60 batches.
NUM_EPOCHS = 3
# ─────────────────────────────────────────

def main():
    # BUG FIX: Guard against running the training script before data prep
    if not os.path.exists(DATA_FILE):
        print(f"ERROR: '{DATA_FILE}' not found!")
        print("Please run 'python prepare_data.py' first.")
        sys.exit(1)

    print(f"Loading base model: {MODEL_NAME}...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=None,
        load_in_4bit=True,
    )

    print("Applying LoRA adapters...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=3407,
        use_rslora=False,
        loftq_config=None,
    )

    # Apply Gemma-specific chat template to the tokenizer
    tokenizer = get_chat_template(tokenizer, chat_template="gemma")

    print(f"Loading dataset from '{DATA_FILE}'...")
    dataset = load_dataset("json", data_files=DATA_FILE, split="train")
    print(f"Dataset size: {len(dataset):,} examples")

    def formatting_prompts_func(examples):
        convos = examples["messages"]
        # BUG FIX: add_generation_prompt=False is correct for training data
        # (we include the full assistant turn). This was already correct.
        texts = [
            tokenizer.apply_chat_template(
                convo, tokenize=False, add_generation_prompt=False
            )
            for convo in convos
        ]
        return {"text": texts}

    print("Formatting dataset...")
    dataset = dataset.map(formatting_prompts_func, batched=True, num_proc=2)

    # BUG FIX: Removed hardcoded max_steps=60. Now uses num_train_epochs=3 so
    # the model trains on the full dataset 3 times regardless of size.
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LENGTH,
        dataset_num_proc=2,
        packing=True,  # BUG FIX: Enable packing for much faster training throughput
        args=TrainingArguments(
            num_train_epochs=NUM_EPOCHS,
            per_device_train_batch_size=2,
            gradient_accumulation_steps=4,
            warmup_ratio=0.05,           # BUG FIX: warmup_ratio scales better than fixed warmup_steps
            learning_rate=2e-4,
            fp16=not is_bfloat16_supported(),
            bf16=is_bfloat16_supported(),
            logging_steps=10,
            save_strategy="epoch",       # BUG FIX: Save a checkpoint after each epoch
            save_total_limit=2,          # Keep only 2 checkpoints to save disk space
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="cosine", # BUG FIX: Cosine decay is smoother than linear for long runs
            seed=3407,
            output_dir="training_outputs",
            report_to="none",           # BUG FIX: Disable W&B/TensorBoard to avoid missing deps errors
        ),
    )

    print("\n" + "=" * 60)
    print(" Starting Training...")
    print("=" * 60)
    trainer_stats = trainer.train()

    print("\n" + "=" * 60)
    print(f" Training Complete!")
    print(f" Total steps: {trainer_stats.global_step}")
    print(f" Final loss:  {trainer_stats.training_loss:.4f}")
    print("=" * 60)

    print(f"\nSaving LoRA model to '{OUTPUT_DIR}'...")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"✓ Done! Your NPC Brain is saved in the '{OUTPUT_DIR}' folder.")


if __name__ == "__main__":
    main()
