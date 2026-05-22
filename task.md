# Game NPC Engine — Master Build Task List

## Feature 1: Behavioral Constitution (Anti-Jailbreak)
- `[x]` Create `core/constitution.py`
- `[x]` Integrated into master `npc_api.py`

## Feature 2: Eternal Memory (SQLite)
- `[x]` Create `core/memory_db.py`
- `[x]` Integrated into master `npc_api.py`

## Feature 3: Living World Injection
- `[x]` Create `core/world_state.py`
- `[x]` Create `world_state.json`
- `[x]` Add `/world` PUT/GET endpoints to API

## Feature 4: Emotional Prosody Engine
- `[x]` Create `core/emotion_voice.py`
- `[x]` Integrated into master `npc_api.py`

## Feature 5: NPC Gossip Network
- `[x]` Create `core/gossip_engine.py`
- `[x]` Create `gossip_networks.json`
- `[x]` Add `/gossip` POST endpoint to API

## Feature 6: NPC Simulation Sandbox (Stress Tester)
- `[x]` Create `tools/npc_stress_test.py`

## Game Engine SDKs
- `[x]` Unity SDK (`sdk/unity/Unity_NPC_Client.cs`)
- `[x]` Unreal Engine C++ Header (`sdk/unreal/NPCEnginePlugin.h`)
- `[x]` Unreal Engine C++ Source (`sdk/unreal/NPCEnginePlugin.cpp`)
- `[x]` Godot GDScript SDK (`sdk/godot/NPCEngineClient.gd`)

## Documentation
- `[x]` Master API wired with all 7 features
