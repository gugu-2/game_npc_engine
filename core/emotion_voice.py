"""
Feature 4: Emotional Prosody Engine
=====================================
Automatically selects the correct voice reference .wav based on the emotion
tag returned by the LLM. Instead of one flat voice, each NPC has a library
of emotion-tagged voice clips so they actually SOUND how they FEEL.

Voice Directory Convention:
  voices/
    grom/
      neutral.wav
      angry.wav
      happy.wav
      sad.wav
      fearful.wav
      surprised.wav
    elara/
      neutral.wav
      happy.wav
      ...

If a specific emotion clip is missing, the system falls back gracefully.
"""

import os
import re
from typing import Optional

VOICES_DIR = os.path.join(os.path.dirname(__file__), "..", "voices")

# Emotion fallback chain — if a clip is missing, try a related emotion
EMOTION_FALLBACK: dict[str, list[str]] = {
    "neutral":   ["neutral", "happy"],
    "happy":     ["happy", "neutral"],
    "angry":     ["angry", "neutral"],
    "sad":       ["sad", "neutral"],
    "fearful":   ["fearful", "sad", "neutral"],
    "surprised": ["surprised", "happy", "neutral"],
    "suspicious":["angry", "neutral"],
    "disgusted": ["angry", "neutral"],
    "excited":   ["happy", "surprised", "neutral"],
}


def resolve_voice_path(character_name: str, emotion: str) -> Optional[str]:
    """
    Given an NPC name and emotion, returns the best matching .wav file path.
    Uses the fallback chain if the exact emotion clip is not available.

    Convention: voices/<character_name_lowercase>/<emotion>.wav

    Returns None if no voice files exist for this character.
    """
    char_dir = os.path.join(VOICES_DIR, character_name.lower().replace(" ", "_"))

    if not os.path.isdir(char_dir):
        return None

    # Try the fallback chain
    fallback_chain = EMOTION_FALLBACK.get(emotion.lower(), [emotion, "neutral"])

    for candidate_emotion in fallback_chain:
        candidate_path = os.path.join(char_dir, f"{candidate_emotion}.wav")
        if os.path.exists(candidate_path):
            return candidate_path

    # Last resort: pick ANY .wav in the character's folder
    for f in os.listdir(char_dir):
        if f.endswith(".wav"):
            return os.path.join(char_dir, f)

    return None


def list_available_voices() -> dict[str, list[str]]:
    """
    Returns a dictionary of all available characters and their emotion clips.
    Useful for the /voices endpoint and developer debugging.
    """
    result = {}
    if not os.path.isdir(VOICES_DIR):
        return result

    for char_dir in os.scandir(VOICES_DIR):
        if char_dir.is_dir():
            emotions = [
                f[:-4] for f in os.listdir(char_dir.path) if f.endswith(".wav")
            ]
            if emotions:
                result[char_dir.name] = sorted(emotions)

    return result


def create_voice_directory(character_name: str):
    """Creates the voice directory structure for a new NPC character."""
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", character_name.lower())
    char_dir = os.path.join(VOICES_DIR, safe_name)
    os.makedirs(char_dir, exist_ok=True)
    readme_path = os.path.join(char_dir, "README.txt")
    with open(readme_path, "w") as f:
        f.write(
            f"Voice clips for '{character_name}'\n\n"
            "Add short 3-5 second .wav recordings:\n"
            "  neutral.wav   — default speaking voice\n"
            "  angry.wav     — when the NPC is angry\n"
            "  happy.wav     — when the NPC is happy\n"
            "  sad.wav       — when the NPC is sad\n"
            "  fearful.wav   — when the NPC is scared\n"
            "  surprised.wav — when the NPC is surprised\n\n"
            "The engine will automatically pick the right voice based on the AI's emotion output.\n"
        )
    print(f"Created voice directory: {char_dir}")
    return char_dir
