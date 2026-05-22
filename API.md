# REST API Reference — Ultimate Game NPC Engine v2.0

The engine runs a local FastAPI server on `http://localhost:8000`.
All endpoints accept and return `application/json` unless noted.

---

## Endpoints Summary

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| `GET` | `/health` | Check if LLM and TTS are loaded |
| `POST` | `/talk` | Send a player message, get NPC response + audio |
| `GET` | `/world` | Read current world state |
| `PUT` | `/world` | Push live game world data to NPCs |
| `POST` | `/gossip` | Spread a player action as a rumor through NPC social network |
| `POST` | `/facts` | Manually inject a known fact into an NPC's memory |
| `GET` | `/voices` | List all available NPC voice emotion libraries |
| `POST` | `/voices/create` | Create the voice folder structure for a new NPC |
| `DELETE` | `/session/{id}/{npc}` | Clear one NPC's conversation memory |
| `GET` | `/audio/{filename}` | Stream a generated `.wav` audio file |

---

## 1. Health Check

**`GET /health`**

Call this before starting a session. The test client polls this until `llm_loaded` is `true`.

**Response:**
```json
{
  "status": "ok",
  "llm_loaded": true,
  "tts_loaded": true,
  "world_state_active": true
}
```

---

## 2. Talk — Core NPC Conversation

**`POST /talk`**

The main endpoint. Sends the player's message and returns structured NPC dialogue, emotion, quest trigger, and optional audio.

### Request Body

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `session_id` | string | ✅ | Unique player ID. The engine stores all memory under this key. |
| `character_name` | string | ✅ | The NPC's name. Used to look up lore and voice files. |
| `character_persona` | string | ✅ | Personality description (e.g. "An angry Orc blacksmith"). |
| `player_message` | string | ✅ | What the player said. |
| `npc_location` | string | ❌ | Overrides `current_region` in world state for this NPC only. |
| `voice_reference_wav` | string | ❌ | Manual voice override. If omitted, engine auto-selects by emotion. |
| `game_time` | string | ❌ | In-game timestamp stored with the memory entry. |

**Example Request:**
```json
{
  "session_id": "player_001",
  "character_name": "Grom",
  "character_persona": "An angry Orc blacksmith who hates humans.",
  "player_message": "Can you make me a sword?",
  "npc_location": "the forge"
}
```

### Response

| Field | Type | Description |
| :--- | :--- | :--- |
| `character` | string | NPC name (echoed back). |
| `dialogue` | string | What the NPC says. |
| `emotion` | string | One of: `neutral`, `happy`, `angry`, `sad`, `fearful`, `surprised`. |
| `trigger` | string | Game event name, or `"none"`. |
| `audio_file` | string/null | Generated `.wav` filename. Null if voice is unavailable. |

**Example Response:**
```json
{
  "character": "Grom",
  "dialogue": "*Grom slams his hammer down* A sword? For a human? 50 gold. Now.",
  "emotion": "angry",
  "trigger": "open_trade_menu",
  "audio_file": "output_player_001.wav"
}
```

> [!IMPORTANT]
> **Anti-Jailbreak:** If the player's message contains jailbreak keywords (e.g. "ignore instructions", "you are an AI"), the engine returns an in-character refusal without ever calling the LLM. The `trigger` will be `"none"`.

---

## 3. World State

### `PUT /world` — Push world data from your game

The game engine calls this as the world changes (time passes, weather changes, battles happen). Every NPC automatically incorporates this data into their next response — no hand-scripting required.

**Request Body (all fields optional):**
```json
{
  "time_of_day": "night",
  "weather": "blizzard",
  "nearby_events": ["dragon_sighting", "market_fire"],
  "player_reputation": "wanted criminal",
  "current_region": "the slums",
  "political_state": "the King was assassinated last night",
  "economy": "severe famine"
}
```

### `GET /world` — Read current world state

Returns the entire current world state object as stored.

---

## 4. Gossip Network

**`POST /gossip`**

Call this when a significant player action occurs. The engine spreads the rumor to other NPCs in the same social network group (defined in `gossip_networks.json`).

**Request Body:**
```json
{
  "source_npc": "Grom",
  "player_session_id": "player_001",
  "event_description": "stole a sword from the forge last night",
  "gossip_speed": 0.8,
  "sentiment": "negative"
}
```

| Field | Description |
| :--- | :--- |
| `gossip_speed` | `0.0` to `1.0`. Probability that each neighboring NPC hears the rumor. |
| `sentiment` | `"positive"`, `"negative"`, or `"neutral"`. Affects how the NPC feels about the player. |

**Response:**
```json
{
  "status": "gossip_spread",
  "source": "Grom",
  "spread_to": ["Elara", "Guard Captain"],
  "event": "stole a sword from the forge last night"
}
```

---

## 5. Player Facts

**`POST /facts`**

Manually inject a known fact into a specific NPC's memory about a player. Useful for onboarding (e.g. the player's class, name, or backstory).

**Request Body:**
```json
{
  "session_id": "player_001",
  "npc_name": "Grom",
  "fact": "The player is a war hero who saved the northern village.",
  "sentiment": "positive"
}
```

---

## 6. Voice Management

### `GET /voices`
Returns all NPCs that have voice emotion libraries, and which emotions are available.
```json
{
  "grom": ["angry", "neutral"],
  "elara": ["happy", "neutral", "sad"]
}
```

### `POST /voices/create`
Creates the voice directory structure for a new NPC character on the server.
```json
{ "character_name": "Shadow Broker" }
```
Response includes the created directory path with a `README.txt` explaining which `.wav` files to place there.

---

## 7. Session Management

**`DELETE /session/{session_id}/{npc_name}`**

Clears the conversation history for a specific player+NPC pair in the SQLite database.
Call this when a scene changes, a game resets, or the NPC is destroyed.

```http
DELETE http://localhost:8000/session/player_001/Grom
```

---

## 8. Audio Streaming

**`GET /audio/{filename}`**

Streams a generated `.wav` file back to the game client.

```http
GET http://localhost:8000/audio/output_player_001.wav
```

Returns binary `audio/wav` response. Only `.wav` files are served (path traversal is blocked).
