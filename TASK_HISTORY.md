# Task History — Ultimate Game NPC Engine

This document is the complete, justified history of everything built in this project.
It records every task, what was done, why it was done, what files were created or changed, and what bugs were found and fixed.

---

## Phase 1 — Project Setup

### Task 1.1 — New Project Created
**Date:** Session Start
**What:** Created a new folder `game_npc_engine` as a fresh, isolated project separate from the Legal Scanner.
**Why:** The user explicitly wanted a new project. Isolating it prevents any dependency or config collision with other projects.
**Files Created:** `game_npc_engine/` (empty folder)

---

## Phase 2 — Core Architecture (v1.0)

### Task 2.1 — Base Model Decision
**Decision:** Chose `unsloth/gemma-2-2b-it` over Gemma-2 9B.
**Justification:**
- Game NPCs must respond in under 2 seconds. The 9B model is too slow for real-time dialogue.
- The 2B model uses only ~2.5GB VRAM in 4-bit mode, leaving headroom for the game engine to render 3D graphics on the same GPU.
- The 9B model (used for the Legal Scanner) is appropriate for complex reasoning. The 2B model is sufficient for expressive roleplay.
**Files Changed:** `train_npc.py`

### Task 2.2 — Data Pipeline
**What:** Created `prepare_data.py` to download and format the Airoboros 3.2 Roleplay dataset.
**Why:** We need roleplay-specific data, not generic Q&A data. Airoboros is considered one of the highest-quality open-source roleplay datasets.
**Files Created:** `prepare_data.py`, `DATASET.md`

**Bugs fixed in this file:**
- **Empty row poisoning:** Added `format_item()` validator that skips blank/short rows to prevent garbage data from entering training.
- **Category mismatch:** Original filter only matched `"roleplay"`. Fixed to also match `"rp"` as Airoboros uses both labels across versions.
- **Data cap removed:** Original script capped at 2,000 rows. Removed the cap so the full high-quality subset is used.
- **Toy dataset diversity:** Original fallback had 2 templates × 50 (severe overfitting risk). Replaced with 10 diverse, unique NPC archetypes.
- **Exit code:** Script now returns `sys.exit(1)` on failure so CI/CD pipelines know when to stop.

### Task 2.3 — Training Script
**What:** Created `train_npc.py` using Unsloth + QLoRA.
**Files Created:** `train_npc.py`

**Bugs fixed in this file:**
- **`max_steps=60` was critically wrong.** 60 training steps means the model only ever sees 60 batches regardless of how large the dataset is. Changed to `num_train_epochs=3` so all data is used fully.
- **`packing=False`** wastes GPU cycles padding every batch. Enabled `packing=True`.
- **`warmup_steps` replaced with `warmup_ratio`** which scales correctly with dataset size.
- **`lr_scheduler_type`** changed from `"linear"` to `"cosine"` for smoother convergence on longer training runs.
- **Checkpoint saving added:** `save_strategy="epoch"` so you get a recoverable checkpoint after each epoch.
- **`report_to="none"`** added to prevent crashes from missing W&B/TensorBoard dependencies.
- **Data file guard:** Script now checks that `npc_training_data.jsonl` exists before starting, giving a clear error message instead of a cryptic PyTorch crash.

### Task 2.4 — Initial API
**What:** Created `npc_api.py` as a FastAPI server.
**Files Created:** `npc_api.py`

**Bugs fixed in original version:**
- `temperature=0.7` was silently ignored because `do_sample=True` was missing.
- `str = None` is wrong Pydantic v2 typing — fixed to `Optional[str] = None`.
- JSON parsing only stripped ` ```json ` prefix, missing many other malformed AI outputs.
- No CORS headers — Unity and web frontends could not connect.
- No session cleanup endpoint.
- Path traversal vulnerability on `/audio/` endpoint.
- No CUDA availability check before calling `.to("cuda")`.

### Task 2.5 — Unity C# Client
**What:** Created `Unity_NPC_Client.cs` as a drop-in Unity MonoBehaviour component.
**Files Created:** `sdk/unity/Unity_NPC_Client.cs`

**Bugs fixed:**
- JSON built via C# string interpolation would crash if the player typed a `"` character. Fixed with proper `JsonUtility.ToJson()`.
- No timeout on HTTP requests — game would freeze if server died.
- No auto-generated session ID — all NPCs would share the same conversation memory.
- No `IsBusy` guard — player could spam the NPC and flood the server with requests.

### Task 2.6 — Initial Test Client
**What:** Created `test_chat.py` for terminal-based NPC testing.
**Files Created:** `test_chat.py`

**Bugs fixed:**
- No health check — client crashed if server was still loading the model.
- Hardcoded session ID — old conversations leaked into new test runs.
- Audio file deleted while `pygame` still held the OS file lock.

---

## Phase 3 — The 7 Game-Changing Features (v2.0)

### Task 3.1 — Feature 1: Behavioral Constitution (Anti-Jailbreak)
**What:** Created `core/constitution.py`.
**Why:** Studios refuse to ship AI NPCs because players can jailbreak them. Solving this is the single biggest enterprise sales unlock.
**Files Created:** `core/constitution.py`
**How it works:**
1. **Pre-flight keyword check:** 20+ jailbreak terms are scanned on the raw player message BEFORE the LLM is called. If detected, the LLM is never invoked.
2. **Iron Lock Prefix:** A hardcoded system block is always prepended to the prompt that explicitly tells the model it cannot know what "AI", "LLM", or "system prompt" means.
3. **In-character refusal pool:** If jailbreak is detected, a random immersive refusal response is returned — no error, no broken experience.

### Task 3.2 — Feature 2: Eternal Memory (SQLite)
**What:** Created `core/memory_db.py`.
**Why:** Old in-memory dict was lost on every server restart. SQLite survives restarts and provides cross-session memory.
**Files Created:** `core/memory_db.py`, `npc_memory.db` (auto-created on first run)
**3 Tables:**
- `conversations` — full message history per session+NPC
- `player_facts` — known facts the NPC has learned about the player
- `npc_events` — events the NPC witnessed or heard as gossip

### Task 3.3 — Feature 3: Living World Injection
**What:** Created `core/world_state.py`, `world_state.json`.
**Why:** NPCs in all existing games are "blind" to the world. A developer currently needs thousands of hand-scripted conditions for NPCs to react to weather, time, and events. We inject it automatically from a JSON feed.
**Files Created:** `core/world_state.py`, `world_state.json`

### Task 3.4 — Feature 4: Emotional Prosody Engine
**What:** Created `core/emotion_voice.py`.
**Why:** XTTS-v2 voice cloning is flat with one reference clip. By matching the reference clip to the LLM's `emotion` output, the NPC voice actually sounds angry when it is angry.
**Files Created:** `core/emotion_voice.py`
**Convention:** `voices/<character_name>/<emotion>.wav`

### Task 3.5 — Feature 5: NPC Gossip Network
**What:** Created `core/gossip_engine.py`, `gossip_networks.json`.
**Why:** This is the most-requested feature in game AI — never shipped by any competitor. NPCs being aware of what happened in other conversations creates genuine world-aliveness.
**Files Created:** `core/gossip_engine.py`, `gossip_networks.json`

### Task 3.6 — Feature 6: NPC Simulation Sandbox
**What:** Created `tools/npc_stress_test.py`.
**Why:** Studios need automated QA to verify NPC behavior before shipping. A 3-week manual QA job is now a 10-minute automated run.
**Files Created:** `tools/npc_stress_test.py`
**Test Suites:** Normal inputs, Lore questions, Jailbreak attacks, Edge cases.
**Output:** `tools/stress_test_report.html` with full pass/fail/timing data.

### Task 3.7 — Feature 7: 100% Local (Zero API Cost)
**No new code required.** This is the architectural foundation of the entire project.
The entire engine runs locally. Zero external API calls. Zero monthly fees.
Competitors charge $0.01/message. At 1M players × 50 messages = $500,000/month. This engine costs $0.00/month after initial setup.

---

## Phase 4 — Multi-Engine SDK Expansion

### Task 4.1 — Unreal Engine 5 SDK
**What:** Created C++ `UActorComponent` plugin.
**Files Created:** `sdk/unreal/NPCEnginePlugin.h`, `sdk/unreal/NPCEnginePlugin.cpp`
**Features exposed as Blueprint delegates:**
- `OnDialogueReceived` — fires with full `FNPCResponse` struct
- `OnQuestTriggered` — fires with the trigger string
- `OnError` — fires with error message
**Blueprint-callable functions:** `SpeakToNPC()`, `ClearMemory()`, `ReportGossipEvent()`, `UpdateWorldState()`

### Task 4.2 — Godot 4 SDK
**What:** Created GDScript `Node` script with Godot signals.
**Files Created:** `sdk/godot/NPCEngineClient.gd`
**Signals:** `dialogue_received`, `quest_triggered`, `error_occurred`
**Methods:** `speak_to_npc()`, `clear_memory()`, `report_gossip()`, `update_world_state()`

---

## Phase 5 — Bug Fixes (Post-Implementation Audit)

### Task 5.1 — Missing `core/__init__.py`
**Bug:** Python would fail to find `core.constitution`, `core.memory_db`, etc. because the `core/` directory was not a Python package.
**Fix:** Created `core/__init__.py`.
**Severity:** CRITICAL — the entire API would fail to start.

### Task 5.2 — Gossip Engine Used `sys.path` Hack
**Bug:** `gossip_engine.py` used `sys.path.insert(0, ...)` to find `memory_db.py`. This breaks when the module is imported from a different working directory.
**Fix:** Changed to `from core.memory_db import ...` (proper package import).
**Severity:** HIGH — gossip would fail to save events in production.

### Task 5.3 — Lore.json Read on Every API Request
**Bug:** `lore.json` was opened, read, and closed on every single `/talk` call. At 100 req/sec this is 100 unnecessary disk reads per second.
**Fix:** Load lore.json once at startup into `_LORE_DB` module-level variable.
**Severity:** MEDIUM — performance degradation under load.

### Task 5.4 — Health Endpoint Called `load_world_state()` (Disk Read on Every Poll)
**Bug:** The `/health` endpoint called `load_world_state()` which reads `world_state.json` from disk. Unity and test clients poll this every 2 seconds.
**Fix:** Changed to `get_raw_state()` which returns the already-cached in-memory dict.
**Severity:** MEDIUM — unnecessary disk I/O on every health poll.

### Task 5.5 — API.md Outdated
**Bug:** `API.md` documented only 3 endpoints. After v2.0, the API has 10 endpoints.
**Fix:** Completely rewrote `API.md` to document all 10 endpoints with request/response examples.
**Severity:** LOW — documentation only, no runtime impact.

---

## Current File Tree

```
game_npc_engine/
├── core/
│   ├── __init__.py         ← Makes core a Python package
│   ├── constitution.py     ← Feature 1: Anti-Jailbreak
│   ├── memory_db.py        ← Feature 2: Eternal Memory (SQLite)
│   ├── world_state.py      ← Feature 3: Living World Injection
│   ├── emotion_voice.py    ← Feature 4: Emotional Prosody
│   └── gossip_engine.py    ← Feature 5: Gossip Network
├── sdk/
│   ├── unity/
│   │   └── Unity_NPC_Client.cs
│   ├── unreal/
│   │   ├── NPCEnginePlugin.h
│   │   └── NPCEnginePlugin.cpp
│   └── godot/
│       └── NPCEngineClient.gd
├── tools/
│   └── npc_stress_test.py  ← Feature 6: Stress Tester
├── voices/                 ← Feature 4: Emotion Voice Files
│   └── <character>/<emotion>.wav
├── npc_api.py              ← Master API (all 7 features wired)
├── prepare_data.py         ← Dataset download + formatting
├── train_npc.py            ← QLoRA fine-tuning script
├── test_chat.py            ← Terminal test client
├── lore.json               ← World lore database
├── gossip_networks.json    ← NPC social network groups
├── world_state.json        ← Live world state template
├── requirements.txt
├── README.md
├── API.md
├── ARCHITECTURE.md
├── DATASET.md
├── FEATURES.md
├── GAME_CHANGERS.md
├── INTEGRATION.md
├── SETUP.md
├── TRAINING_WORKFLOW.md
└── TASK_HISTORY.md         ← This file
```
