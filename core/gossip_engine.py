"""
Feature 5: NPC Gossip Network
================================
NPCs talk to each other when the player is NOT around.
When a significant player action occurs, the game engine fires a gossip event.
The gossip engine then propagates the "rumor" to nearby NPCs asynchronously,
injecting it into their long-term memory so they react differently next time.

This is the feature NO competitor has ever shipped. It makes the game world
feel alive — NPCs are social beings who share information.

Gossip Flow:
  1. Player robs Grom's shop.
  2. Unity calls POST /gossip with the event.
  3. The gossip engine distributes the rumor to Elara, the Guard, the Innkeeper.
  4. Each NPC's memory is updated with the rumor as a "heard" event.
  5. Next conversation with any of them — they react accordingly.
"""

import json
import random
import os
from typing import Optional
from datetime import datetime

# Proper package-level import (requires core/__init__.py to exist)
from core.memory_db import save_event, save_player_fact

# How far a rumor spreads — NPCs not in this group never hear it
GOSSIP_NETWORKS: dict[str, list[str]] = {}
_NETWORKS_FILE = os.path.join(os.path.dirname(__file__), "..", "gossip_networks.json")


def load_gossip_networks():
    """Loads developer-defined gossip networks from JSON."""
    global GOSSIP_NETWORKS
    try:
        if os.path.exists(_NETWORKS_FILE):
            with open(_NETWORKS_FILE, "r", encoding="utf-8") as f:
                GOSSIP_NETWORKS = json.load(f)
            print(f"Gossip networks loaded: {list(GOSSIP_NETWORKS.keys())}")
    except Exception as e:
        print(f"Warning: Could not load gossip_networks.json: {e}")


def spread_rumor(
    source_npc: str,
    player_session_id: str,
    event_description: str,
    gossip_speed: float = 0.7,
    sentiment: str = "negative",
):
    """
    Spreads a rumor from the source NPC to its gossip network.

    Args:
        source_npc:         The NPC who witnessed the event.
        player_session_id:  The player involved.
        event_description:  What happened (e.g., "stole a sword from the forge").
        gossip_speed:       0.0-1.0. How likely each neighbor NPC is to hear it.
        sentiment:          "positive", "negative", or "neutral".
    """
    # Record the event for the source NPC itself (witnessed, not gossip)
    save_event(source_npc, event_description, source="witnessed")
    save_player_fact(player_session_id, source_npc, event_description, sentiment)

    # Find the gossip network this NPC belongs to
    network = []
    for network_name, members in GOSSIP_NETWORKS.items():
        if source_npc in members:
            network = [m for m in members if m != source_npc]
            break

    if not network:
        # No network defined — gossip to nobody
        return {"source": source_npc, "spread_to": [], "event": event_description}

    spread_to = []
    for neighbor_npc in network:
        # Probabilistic spread — not every NPC hears every rumor immediately
        if random.random() < gossip_speed:
            rumor_text = f"Heard from {source_npc}: The player {event_description}."
            save_event(neighbor_npc, rumor_text, source="gossip")
            save_player_fact(player_session_id, neighbor_npc, rumor_text, sentiment)
            spread_to.append(neighbor_npc)

    print(f"Gossip spread from {source_npc} to: {spread_to}")
    return {"source": source_npc, "spread_to": spread_to, "event": event_description}


def get_recent_rumors(npc_name: str, limit: int = 3) -> list[str]:
    """Returns recent gossip events an NPC has heard."""
    from core.memory_db import load_npc_events
    return load_npc_events(npc_name, limit=limit)
