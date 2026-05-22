"""
Feature 3: Living World Injection
===================================
Maintains a global "world state" that is automatically injected into every
NPC prompt before generation. Game engines push live world data to the API,
and every NPC instantly "knows" what is happening in the world.

Example: The player walks into a burning village at midnight during a blizzard.
Without any hand-scripting, every NPC in that village automatically reacts
to the fire, the weather, and the time of day.
"""

import json
import os
from typing import Optional
from datetime import datetime

_WORLD_STATE: dict = {}
_STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "world_state.json")


def load_world_state() -> dict:
    """Load world state from disk on startup."""
    global _WORLD_STATE
    try:
        if os.path.exists(_STATE_FILE):
            with open(_STATE_FILE, "r", encoding="utf-8") as f:
                _WORLD_STATE = json.load(f)
            print(f"World state loaded: {list(_WORLD_STATE.keys())}")
    except Exception as e:
        print(f"Warning: Could not load world_state.json: {e}")
    return _WORLD_STATE


def update_world_state(updates: dict) -> dict:
    """
    Called by the game engine via the /world PUT endpoint.
    Merges new data into the global state and saves to disk.
    """
    global _WORLD_STATE
    _WORLD_STATE.update(updates)
    _WORLD_STATE["last_updated"] = datetime.utcnow().isoformat()
    try:
        with open(_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(_WORLD_STATE, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save world state: {e}")
    return _WORLD_STATE


def get_world_context_string(npc_location: Optional[str] = None) -> str:
    """
    Converts the current world state into a natural language paragraph
    that can be injected into the NPC's system prompt.
    """
    if not _WORLD_STATE:
        return ""

    parts = []

    # Time of day
    if "time_of_day" in _WORLD_STATE:
        parts.append(f"It is currently {_WORLD_STATE['time_of_day']}.")

    # Weather
    if "weather" in _WORLD_STATE:
        parts.append(f"The weather is {_WORLD_STATE['weather']}.")

    # Nearby events (most dramatic first)
    events = _WORLD_STATE.get("nearby_events", [])
    if events:
        event_str = ", ".join(events)
        parts.append(f"Nearby events you are aware of: {event_str}.")

    # Player reputation
    if "player_reputation" in _WORLD_STATE:
        rep = _WORLD_STATE["player_reputation"]
        parts.append(f"The player talking to you is known as: {rep}.")

    # Current region
    region = npc_location or _WORLD_STATE.get("current_region")
    if region:
        parts.append(f"You are located in: {region}.")

    # Economic state
    if "economy" in _WORLD_STATE:
        parts.append(f"Economic conditions: {_WORLD_STATE['economy']}.")

    # Active wars / political state
    if "political_state" in _WORLD_STATE:
        parts.append(f"Political situation: {_WORLD_STATE['political_state']}.")

    if not parts:
        return ""

    return "\n\n[CURRENT WORLD STATE — Use this to inform your response naturally]:\n" + " ".join(parts)


def get_raw_state() -> dict:
    return _WORLD_STATE.copy()
