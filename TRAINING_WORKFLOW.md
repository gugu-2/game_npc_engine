# Training Workflow (For AI Agents & Developers)

**Target Audience:** AI Coding Assistants, MLOps Engineers, Data Scientists.
**Objective:** Fine-tune the Gemma-2 2B model on an RPG conversation dataset using Unsloth (QLoRA) on a secondary machine equipped with an NVIDIA GPU and WSL.

---

## 1. Environment Requirements
The training machine **must** have WSL (Ubuntu) installed if running on Windows. Unsloth requires Linux to compile Triton kernels for maximum VRAM efficiency and speed.

**Setup Commands:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
pip install --no-deps "xformers<0.0.27" "trl<0.9.0" peft accelerate bitsandbytes
pip install datasets torch transformers
```

## 2. Data Preparation Pipeline
**Script:** `prepare_data.py`

**Logic Flow:**
1. Connects to Hugging Face and pulls the `jondurbin/airoboros-3.2` dataset.
2. Filters the dataset exclusively for the `"roleplay"` category.
3. Formats the data into the standard **Gemma Chat Format**:
   ```json
   {"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
   ```
4. Saves the output to `npc_training_data.jsonl`.
*Note: If network failures occur, the script has a fallback method to generate a high-quality "Toy Dataset" programmatically.*

## 3. Training Pipeline
**Script:** `train_npc.py`

**Model Choice Rationale:**
We use `unsloth/gemma-2-2b-it`. We do **not** use the 9B parameter model. Game engines require lightning-fast inference (< 1.5 seconds) and minimal VRAM overhead (so the GPU can render game graphics). Gemma-2 2B fits in ~2.5GB of VRAM when quantized to 4-bit, making it the perfect candidate.

**Hyperparameters:**
- **Quantization:** 4-bit (via bitsandbytes natively integrated in Unsloth).
- **LoRA Rank (r):** 16 (Targets Q, K, V, O, Gate, Up, Down projections).
- **Batch Size:** 2 (with gradient accumulation of 4).
- **Optimizer:** `adamw_8bit` (crucial for keeping memory low on RTX 50-series consumer cards).

**Execution:**
Run `python train_npc.py`. 
Upon completion, the script saves the LoRA adapters and the tokenizer to the `/npc_lora_model` directory.

## 4. Post-Training Handoff
Once training is complete, the `npc_lora_model` directory is copied back to the deployment machine. The `npc_api.py` script automatically detects this directory and loads the fine-tuned weights on top of the base model via `FastLanguageModel.from_pretrained()`.
