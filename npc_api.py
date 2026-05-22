"""
Ultimate Game NPC Engine — Master API
All 7 game-changing features wired together.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, validator
from typing import Optional
import uvicorn, torch, json, os, re, warnings
warnings.filterwarnings("ignore")

# ── Feature Modules ──────────────────────────────────────────────────────
from core.constitution  import build_constitution_prompt, detect_jailbreak, get_refusal_response
from core.memory_db     import (initialize_database, save_message, load_history,
                                 save_player_fact, load_player_facts,
                                 save_event, load_npc_events, delete_session)
from core.world_state   import load_world_state, update_world_state, get_world_context_string
from core.emotion_voice import resolve_voice_path, list_available_voices, create_voice_directory
from core.gossip_engine import load_gossip_networks, spread_rumor
# ─────────────────────────────────────────────────────────────────────────

app = FastAPI(title="Ultimate Game NPC Engine", version="2.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Globals
llm_model = None
tokenizer  = None
tts_engine = None
models_loaded = False

# Cache lore once at startup — not on every request
_LORE_DB: dict = {}


# ── Request / Response Models ─────────────────────────────────────────────
class ChatRequest(BaseModel):
    session_id: str
    character_name: str
    character_persona: str
    player_message: str
    npc_location: Optional[str] = None
    voice_reference_wav: Optional[str] = None   # Overrides emotion auto-select if provided
    game_time: Optional[str] = None

    @validator("session_id","character_name","character_persona","player_message")
    def must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Field must not be empty.")
        return v.strip()

class WorldStateUpdate(BaseModel):
    time_of_day: Optional[str] = None
    weather: Optional[str] = None
    nearby_events: Optional[list[str]] = None
    player_reputation: Optional[str] = None
    current_region: Optional[str] = None
    political_state: Optional[str] = None
    economy: Optional[str] = None

class GossipEvent(BaseModel):
    source_npc: str
    player_session_id: str
    event_description: str
    gossip_speed: float = 0.7
    sentiment: str = "negative"

class PlayerFactRequest(BaseModel):
    session_id: str
    npc_name: str
    fact: str
    sentiment: str = "neutral"

class CreateVoiceRequest(BaseModel):
    character_name: str


# ── JSON Extractor ────────────────────────────────────────────────────────
def _extract_json(text: str) -> dict:
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*?\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return {"dialogue": text, "emotion": "neutral", "trigger": "none"}


# ── Engine Loader ─────────────────────────────────────────────────────────
def load_engines():
    global llm_model, tokenizer, tts_engine, models_loaded, _LORE_DB
    # Initialise all subsystems
    initialize_database()
    load_world_state()
    load_gossip_networks()

    # Load lore once at startup
    lore_path = os.path.join(os.path.dirname(__file__), "lore.json")
    try:
        with open(lore_path, encoding="utf-8") as f:
            _LORE_DB = json.load(f)
        print(f"Lore loaded for: {list(_LORE_DB.keys())}")
    except FileNotFoundError:
        print("lore.json not found — lore injection disabled.")
    except Exception as e:
        print(f"Warning: lore.json parse error: {e}")

    model_dir = os.path.join(os.path.dirname(__file__), "npc_lora_model")
    if not os.path.isdir(model_dir):
        print(f"WARNING: Trained model not found at '{model_dir}'. Text generation disabled.")
        return

    try:
        from unsloth import FastLanguageModel
        from unsloth.chat_templates import get_chat_template
        print("Loading LLM Engine (Gemma-2-2B) ...")
        llm_model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=model_dir, max_seq_length=2048, dtype=None, load_in_4bit=True)
        FastLanguageModel.for_inference(llm_model)
        tokenizer = get_chat_template(tokenizer, chat_template="gemma")

        try:
            from TTS.api import TTS as CoquiTTS
            device = "cuda" if torch.cuda.is_available() else "cpu"
            tts_engine = CoquiTTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
            print(f"TTS Engine loaded on {device}.")
        except Exception as e:
            print(f"TTS load failed ({e}). Voice disabled.")

        models_loaded = True
        print("All engines ready!")
    except Exception as e:
        print(f"CRITICAL: LLM load failed: {e}")


@app.on_event("startup")
def startup_event():
    load_engines()


# ── Health ─────────────────────────────────────────────────────────────────
@app.get("/health")
def health_check():
    from core.world_state import get_raw_state
    return {
        "status": "ok",
        "llm_loaded": llm_model is not None,
        "tts_loaded": tts_engine is not None,
        "world_state_active": bool(get_raw_state()),
    }


# ── Core Chat Endpoint ─────────────────────────────────────────────────────
@app.post("/talk")
async def talk_to_npc(req: ChatRequest):
    if not models_loaded:
        raise HTTPException(503, "AI engine not loaded. Check server logs.")

    # ── FEATURE 1: Anti-Jailbreak Constitution ────────────────────────────
    if detect_jailbreak(req.player_message):
        refusal = get_refusal_response(req.character_name)
        save_message(req.session_id, req.character_name, "user", req.player_message, req.game_time)
        save_message(req.session_id, req.character_name, "assistant", json.dumps(refusal), req.game_time)
        return {"character": req.character_name, "audio_file": None, **refusal}

    # ── FEATURE 2: Eternal Memory (SQLite) ───────────────────────────────
    history       = load_history(req.session_id, req.character_name, max_turns=20)
    player_facts  = load_player_facts(req.session_id, req.character_name, limit=5)
    npc_events    = load_npc_events(req.character_name, limit=3)

    facts_str  = (" Player history you remember: " + "; ".join(player_facts)) if player_facts else ""
    events_str = (" Recent events: " + "; ".join(npc_events)) if npc_events else ""

    # ── FEATURE 3: Living World Injection ────────────────────────────────
    world_context = get_world_context_string(npc_location=req.npc_location)

    # Use cached lore (loaded once at startup)
    lore_facts = _LORE_DB.get(req.character_name, [])
    lore_str   = (" Lore facts: " + " ".join(lore_facts)) if lore_facts else ""

    # ── FEATURE 1: Build Hardened Prompt ─────────────────────────────────
    system_prompt = build_constitution_prompt(
        character_name=req.character_name,
        character_persona=req.character_persona + facts_str + events_str + lore_str,
        lore_context=world_context
    )

    # Build message list
    messages = [{"role": "system", "content": system_prompt}] + history
    messages.append({"role": "user", "content": req.player_message})

    # ── LLM Generation ────────────────────────────────────────────────────
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        inputs = tokenizer.apply_chat_template(
            messages, tokenize=True, add_generation_prompt=True, return_tensors="pt").to(device)
        outputs = llm_model.generate(
            input_ids=inputs, max_new_tokens=150, use_cache=True,
            temperature=0.7, do_sample=True, repetition_penalty=1.1)
        raw = tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True).strip()
    except Exception as e:
        raise HTTPException(500, f"Generation failed: {e}")

    npc_data = _extract_json(raw)
    npc_data.setdefault("dialogue", raw)
    npc_data.setdefault("emotion",  "neutral")
    npc_data.setdefault("trigger",  "none")

    # ── Persist to Eternal Memory ─────────────────────────────────────────
    save_message(req.session_id, req.character_name, "user",      req.player_message,       req.game_time)
    save_message(req.session_id, req.character_name, "assistant", json.dumps(npc_data),     req.game_time)

    # ── FEATURE 4: Emotional Prosody Voice Selection ──────────────────────
    audio_generated = False
    safe_session    = re.sub(r"[^a-zA-Z0-9_-]", "_", req.session_id)
    audio_path      = f"output_{safe_session}.wav"

    # Auto-select voice by emotion unless developer overrides
    emotion   = npc_data.get("emotion", "neutral")
    ref_audio = req.voice_reference_wav or resolve_voice_path(req.character_name, emotion)

    if tts_engine and ref_audio and os.path.exists(ref_audio):
        try:
            tts_engine.tts_to_file(
                text=npc_data["dialogue"], file_path=audio_path,
                speaker_wav=ref_audio, language="en")
            audio_generated = True
        except Exception as e:
            print(f"TTS error: {e}")

    return {
        "character":  req.character_name,
        "dialogue":   npc_data["dialogue"],
        "emotion":    emotion,
        "trigger":    npc_data["trigger"],
        "audio_file": audio_path if audio_generated else None,
    }


# ── Feature 3: World State Endpoints ──────────────────────────────────────
@app.put("/world")
async def update_world(state: WorldStateUpdate):
    """Game engine calls this to push live world data (time, weather, events)."""
    updated = update_world_state(state.dict(exclude_none=True))
    return {"status": "updated", "world_state": updated}

@app.get("/world")
async def get_world():
    return load_world_state()


# ── Feature 5: Gossip Network Endpoint ────────────────────────────────────
@app.post("/gossip")
async def post_gossip(event: GossipEvent):
    """
    Game engine calls this when a significant player action occurs.
    The gossip engine spreads the rumor to nearby NPCs automatically.
    """
    result = spread_rumor(
        source_npc=event.source_npc,
        player_session_id=event.player_session_id,
        event_description=event.event_description,
        gossip_speed=event.gossip_speed,
        sentiment=event.sentiment,
    )
    return {"status": "gossip_spread", **result}


# ── Player Facts Endpoint ──────────────────────────────────────────────────
@app.post("/facts")
async def add_player_fact(req: PlayerFactRequest):
    """Manually record a known fact about a player into an NPC's memory."""
    save_player_fact(req.session_id, req.npc_name, req.fact, req.sentiment)
    return {"status": "saved"}


# ── Voice Management Endpoints ─────────────────────────────────────────────
@app.get("/voices")
async def get_voices():
    """Returns all available NPC voice emotion libraries."""
    return list_available_voices()

@app.post("/voices/create")
async def create_voice(req: CreateVoiceRequest):
    """Creates the voice directory structure for a new NPC character."""
    path = create_voice_directory(req.character_name)
    return {"status": "created", "path": path}


# ── Session Management ─────────────────────────────────────────────────────
@app.delete("/session/{session_id}/{npc_name}")
async def clear_session(session_id: str, npc_name: str):
    delete_session(session_id, npc_name)
    return {"status": "cleared"}


# ── Audio Serving ──────────────────────────────────────────────────────────
@app.get("/audio/{filename}")
async def get_audio(filename: str):
    safe_name = os.path.basename(filename)
    if not safe_name.endswith(".wav"):
        raise HTTPException(400, "Only .wav files served.")
    if os.path.exists(safe_name):
        return FileResponse(safe_name, media_type="audio/wav")
    raise HTTPException(404, "Audio file not found.")

# ── Frontend Dashboard ─────────────────────────────────────────────────────
# This serves the UI. Must be placed at the bottom so it doesn't override API routes.
if os.path.exists(os.path.join(os.path.dirname(__file__), "static")):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("npc_api:app", host="0.0.0.0", port=8000, reload=False)
