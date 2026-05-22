import requests
import os
import time
import json

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
API_URL   = "http://localhost:8000/talk"
AUDIO_URL = "http://localhost:8000/audio"
HEALTH_URL = "http://localhost:8000/health"
# ─────────────────────────────────────────

try:
    import pygame
    pygame.mixer.init()
    has_audio = True
except ImportError:
    has_audio = False


def check_server_health():
    """BUG FIX: Old client had no health check. If the server was still
    loading the 2B model (which takes 20-30 seconds), requests would fail
    silently. We now wait and poll until the server is ready."""
    print("Connecting to NPC Engine server...")
    for attempt in range(30):
        try:
            r = requests.get(HEALTH_URL, timeout=2)
            if r.status_code == 200:
                data = r.json()
                if data.get("llm_loaded"):
                    print(f"✓ Server ready! LLM loaded: {data['llm_loaded']} | TTS loaded: {data['tts_loaded']}")
                    return True
                else:
                    print(f"  Server is up but model is still loading... ({attempt+1}/30)")
        except requests.exceptions.ConnectionError:
            print(f"  Waiting for server to start... ({attempt+1}/30)")
        time.sleep(2)
    print("ERROR: Server did not become ready in time. Is npc_api.py running?")
    return False


def play_audio(filename: str):
    if not has_audio:
        print("  [Audio playback disabled — install pygame to hear the NPC voice]")
        return

    try:
        r = requests.get(f"{AUDIO_URL}/{filename}", timeout=10)
        if r.status_code == 200:
            with open("temp_play.wav", "wb") as f:
                f.write(r.content)

            pygame.mixer.music.load("temp_play.wav")
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            pygame.mixer.music.unload()

            # BUG FIX: Old code could crash if the file was locked by pygame.
            # We only remove after unload() confirms it is released.
            if os.path.exists("temp_play.wav"):
                os.remove("temp_play.wav")
        else:
            print(f"  [Audio fetch failed: HTTP {r.status_code}]")
    except Exception as e:
        print(f"  [Audio playback error: {e}]")


def main():
    print("=" * 60)
    print(" Ultimate Game NPC Engine — Test Client")
    print("=" * 60)

    if not check_server_health():
        return

    print("\nDefine your NPC character:")
    npc_name    = input("  NPC Name (e.g., Grom)      : ").strip() or "Grom"
    npc_persona = input("  NPC Persona                : ").strip() or "An angry Orc blacksmith."

    # BUG FIX: Old client used a hardcoded session ID, meaning
    # every test run continued the same old conversation.
    # We now auto-generate a unique session ID per test run.
    import uuid
    session_id = f"test_{uuid.uuid4().hex[:8]}"
    print(f"  Session ID (auto-generated): {session_id}")

    print("\n  [Optional Voice Cloning]")
    print("  Place a 3-second .wav file of your NPC's voice in this folder.")
    voice_file = input("  Voice Reference WAV path (or press Enter to skip): ").strip() or None

    print(f"\n{'─'*60}")
    print(f"  Chatting with {npc_name}. Type 'quit' to exit, 'reset' to clear memory.")
    print(f"{'─'*60}\n")

    while True:
        user_msg = input("You: ").strip()

        if not user_msg:
            continue

        if user_msg.lower() == "quit":
            print(f"Ending session '{session_id}'.")
            try:
                requests.delete(f"http://localhost:8000/session/{session_id}/{npc_name}", timeout=3)
                print("Session cleared on server.")
            except Exception:
                pass
            break

        if user_msg.lower() == "reset":
            try:
                requests.delete(f"http://localhost:8000/session/{session_id}/{npc_name}", timeout=3)
                print("Memory cleared! Starting fresh conversation.\n")
            except Exception as e:
                print(f"Could not clear session: {e}")
            continue

        payload = {
            "session_id": session_id,
            "character_name": npc_name,
            "character_persona": npc_persona,
            "player_message": user_msg,
            "voice_reference_wav": voice_file,
        }

        try:
            print("  [Generating response...]")
            response = requests.post(API_URL, json=payload, timeout=60)

            if response.status_code == 200:
                data = response.json()

                emotion  = data.get("emotion", "neutral").upper()
                dialogue = data.get("dialogue", "")
                trigger  = data.get("trigger", "none")
                audio    = data.get("audio_file")

                print(f"\n  [{emotion}] {npc_name}: {dialogue}")

                if trigger and trigger.lower() != "none":
                    print(f"\n  *** GAME EVENT TRIGGERED: '{trigger}' ***")

                if audio:
                    print("  [Playing NPC voice...]")
                    play_audio(audio)

                print()

            else:
                # BUG FIX: Old code printed raw response text which could be HTML.
                # We now parse the detail field from FastAPI's error response.
                try:
                    err = response.json().get("detail", response.text)
                except Exception:
                    err = response.text
                print(f"  API Error ({response.status_code}): {err}\n")

        except requests.exceptions.Timeout:
            print("  ERROR: Request timed out. The model might be too slow on this hardware.\n")
        except requests.exceptions.ConnectionError:
            print("  ERROR: Cannot connect to server. Is npc_api.py still running?\n")
        except Exception as e:
            print(f"  Unexpected error: {e}\n")


if __name__ == "__main__":
    main()
