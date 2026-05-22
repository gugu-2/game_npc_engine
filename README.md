# Ultimate Game NPC Engine v2.0

A complete, local, zero-API-cost AI brain for Non-Player Characters (NPCs) in video games.
Built on **Gemma-2 2B** + **Coqui XTTS-v2** with full support for Unity, Unreal Engine 5, and Godot 4.

---

## What Makes This Different

| Competitor Products | This Engine |
| :--- | :--- |
| $0.01 per API call | **$0.00 per call — 100% local** |
| Text-only responses | **Text + Cloned Voice + Emotions** |
| NPCs forget everything | **Permanent SQLite memory across sessions** |
| Static world knowledge | **Live world injection (weather, time, events)** |
| Isolated NPCs | **NPC Gossip Network — NPCs talk to each other** |
| Can be jailbroken | **Behavioral Constitution — cannot be broken** |
| Manual QA only | **Automated Stress Test with HTML report** |

---

## The 7 Features

1. **🛡️ Behavioral Constitution** — 3-layer anti-jailbreak prompt shield. No player can break character. Ever.
2. **🧠 Eternal Memory** — SQLite database. NPCs remember players across sessions, server restarts, and weeks.
3. **🌍 Living World Injection** — Push live game data (weather, time, events) to the API and every NPC reacts automatically.
4. **🎭 Emotional Prosody** — Auto-selects the right voice clip (`angry.wav`, `happy.wav`) based on the LLM's emotion output.
5. **👂 Gossip Network** — Player robs a shop? Every NPC in the social group hears about it before the player walks away.
6. **🧪 Stress Test Sandbox** — Automated 200-test suite with jailbreak resistance scoring and HTML report.
7. **💰 Zero API Cost** — Local inference. 1M players × 50 conversations = **$0.00/month**. Competitors charge **$500,000/month**.

---

## Supported Game Engines

| Engine | Integration File | Language |
| :--- | :--- | :--- |
| **Unity** | `sdk/unity/Unity_NPC_Client.cs` | C# |
| **Unreal Engine 5** | `sdk/unreal/NPCEnginePlugin.h/.cpp` | C++ / Blueprint |
| **Godot 4** | `sdk/godot/NPCEngineClient.gd` | GDScript |

---

## Documentation Index

| Document | Contents |
| :--- | :--- |
| [SETUP.md](SETUP.md) | How to install WSL, Python environment, and run the servers |
| [TRAINING_WORKFLOW.md](TRAINING_WORKFLOW.md) | How to fine-tune the model on a training machine |
| [DATASET.md](DATASET.md) | What dataset is used, why, and how it's formatted |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System flow diagram showing how all components connect |
| [API.md](API.md) | Full REST API reference — all 10 endpoints documented |
| [FEATURES.md](FEATURES.md) | Feature breakdown with usage examples |
| [GAME_CHANGERS.md](GAME_CHANGERS.md) | Business case: the 7 burning problems this engine solves |
| [INTEGRATION.md](INTEGRATION.md) | Step-by-step Unity integration guide |
| [TASK_HISTORY.md](TASK_HISTORY.md) | Complete history of all tasks, decisions, and bug fixes |

---

## Quickstart

### Step 1: Train the model (on your training machine with WSL)
```bash
source venv/bin/activate
python prepare_data.py    # Downloads roleplay dataset
python train_npc.py       # Fine-tunes Gemma-2 2B with QLoRA
```

### Step 2: Start the API server
```bash
python npc_api.py
# Server running at http://localhost:8000
```

### Step 3: Test in terminal
```bash
python test_chat.py
```

### Step 4: Integrate into your game
Copy the appropriate SDK file from the `sdk/` folder into your game engine project.
