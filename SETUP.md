# Setup Guide: Game NPC Engine

Welcome to your Local Game NPC Engine! This folder contains everything you need to create, train, and host AI characters for Unity/Unreal Engine locally.

## Step 1: Prepare the Environment

Because we are doing LoRA fine-tuning, you must run this inside **WSL (Ubuntu)** on your Windows machine to get the best performance from your RTX 5050.

1. Open WSL (Ubuntu).
2. Navigate to this folder:
   ```bash
   cd /mnt/c/Users/majip/Downloads/xllm/game_npc_engine
   ```
3. Create a Python environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
4. Install the requirements (and Unsloth):
   ```bash
   pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
   pip install --no-deps "xformers<0.0.27" "trl<0.9.0" peft accelerate bitsandbytes
   pip install -r requirements.txt
   ```

## Step 2: Download the Data

Run the data preparation script to download conversational roleplay data from HuggingFace and format it.

```bash
python prepare_data.py
```
*(If the dataset fails to download, it automatically generates a high-quality "Toy Dataset" so you can still train immediately).*

## Step 3: Train the NPC Brain (Gemma 2 2B)

We are using **Gemma 2 2B** because it is incredibly fast—perfect for game dialogue.
Start the training:

```bash
python train_npc.py
```
This will take a little while. Once done, it saves your fine-tuned weights to a folder named `npc_lora_model`.

## Step 4: Start the Game Engine API

Game engines (Unity/Unreal) need an API to talk to. We built a lightning-fast FastAPI server to handle this. Start the server:

```bash
python npc_api.py
```

## Step 5: Test Your NPC

Open a **second terminal** (this one can be normal Windows PowerShell), navigate to this folder, and run:

```bash
pip install requests
python test_chat.py
```
You can now create an on-the-fly persona (like an Orc Blacksmith or Elven Healer) and chat with them live!
