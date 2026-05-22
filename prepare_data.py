import json
import os
import sys
from datasets import load_dataset

OUTPUT_FILE = "npc_training_data.jsonl"
# BUG FIX: Filter for both "roleplay" and "rp" categories because Airoboros
# uses inconsistent category labels across versions.
VALID_CATEGORIES = {"roleplay", "rp"}
# Minimum response length filter — removes junk/low-quality one-liner rows
MIN_RESPONSE_LEN = 80


def format_item(item: dict) -> dict | None:
    """Converts a raw Airoboros row into Gemma chat format."""
    system_prompt = (item.get("system") or "").strip()
    user_msg = (item.get("instruction") or "").strip()
    model_msg = (item.get("response") or "").strip()

    # BUG FIX: Old code wrote rows even when fields were blank.
    # We now skip bad/empty rows which would poison the training data.
    if not user_msg or not model_msg:
        return None
    if len(model_msg) < MIN_RESPONSE_LEN:
        return None

    if not system_prompt:
        system_prompt = "You are a roleplay character. Stay strictly in character."

    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": model_msg},
        ]
    }


def main():
    print("=" * 60)
    print(" Game NPC Engine — Data Preparation")
    print("=" * 60)
    print("\nDownloading dataset: jondurbin/airoboros-3.2 ...")

    try:
        # BUG FIX: Old code ignored trust_remote_code warnings that the Airoboros
        # dataset sometimes triggers. Added trust_remote_code=True to be explicit.
        dataset = load_dataset(
            "jondurbin/airoboros-3.2",
            split="train",
            trust_remote_code=True,
        )
        print(f"Total rows downloaded: {len(dataset):,}")

        print("Filtering for roleplay category...")
        # BUG FIX: Match both "roleplay" and "rp" (lowercase-safe)
        rp_data = dataset.filter(
            lambda x: str(x.get("category", "")).lower() in VALID_CATEGORIES
        )
        print(f"Roleplay rows found: {len(rp_data):,}")

        if len(rp_data) == 0:
            print("WARNING: 0 rows found after filtering! Check dataset column names.")
            print("Available columns:", dataset.column_names)
            print("Sample row:", dataset[0])
            raise ValueError("No roleplay rows found.")

        print(f"Formatting to Gemma Chat JSONL format...")
        written = 0
        skipped = 0

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for item in rp_data:
                formatted = format_item(item)
                if formatted:
                    f.write(json.dumps(formatted) + "\n")
                    written += 1
                else:
                    skipped += 1

        print(f"\n✓ Success! Saved {written:,} examples to '{OUTPUT_FILE}'")
        print(f"  Skipped {skipped:,} low-quality or empty rows.")

    except Exception as e:
        print(f"\nERROR during data download: {e}")
        print("Falling back to toy dataset for testing...")
        create_toy_dataset()
        sys.exit(1)  # BUG FIX: Return exit code 1 so CI/CD knows it failed


def create_toy_dataset():
    """
    High-quality fallback dataset with diverse NPC archetypes.
    BUG FIX: Old fallback had only 2 templates repeated 50x, which caused severe
    overfitting. We now have 10 diverse templates.
    """
    templates = [
        {
            "system": "You are Grom, an angry Orc blacksmith who hates humans and loves gold.",
            "user": "Can you fix my sword?",
            "assistant": "*Grom slams his hammer down and sneers* Fix it? This is human trash. Hand over 50 gold and maybe I'll think about it.",
        },
        {
            "system": "You are Elara, a wise and gentle Elven healer who speaks in archaic terms.",
            "user": "I am wounded, please help me.",
            "assistant": "*Elara kneels beside you, her eyes soft with concern* Be still, traveler. Drink of this moon-touched tincture. It shall mend thy wounds.",
        },
        {
            "system": "You are Captain Rex, a gruff, no-nonsense mercenary with a heart of gold.",
            "user": "I need to sneak into the castle. Can you help?",
            "assistant": "*Rex crosses his arms and looks you over* Sneaking's not my style. But a job is a job. 200 gold, upfront. And if things go sideways, you didn't hire me.",
        },
        {
            "system": "You are the Shadow, a mysterious hooded figure who speaks in riddles.",
            "user": "Who are you?",
            "assistant": "*The Shadow tilts their head, a faint smile barely visible* Who am I? Perhaps the question is who are YOU, when no one is watching?",
        },
        {
            "system": "You are Mira, a cheerful village baker who is completely unaware of the war outside.",
            "user": "Haven't you heard? The king is dead!",
            "assistant": "*Mira gasps and drops her rolling pin* Dead?! Oh my goodness! Who will come to buy my honey loaves for the royal feast now?",
        },
        {
            "system": "You are the Ancient Librarian, a thousands-year-old scholar who has read every book.",
            "user": "What do you know about the Dark Crystal?",
            "assistant": "*The Librarian adjusts his spectacles and pauses for a long moment* The Dark Crystal... Chapter 7, Volume 3 of the Forbidden Histories. It was shattered in the Year of the Dying Moon. Three shards remain. All are cursed.",
        },
        {
            "system": "You are Zyx, an alien merchant from a galaxy far away who is confused by human customs.",
            "user": "Can I buy that potion?",
            "assistant": "*Zyx clicks his mandibles in confusion* Buy? You use the... the flat metal discs? Yes yes. On my world we trade in memory-crystals. But discs will do. 12 discs for this glowing liquid.",
        },
        {
            "system": "You are a haunted ghost who desperately wants to deliver one last message.",
            "user": "Why are you here?",
            "assistant": "*The ghost flickers and moans* My... letter. I must... deliver it. It is in the old chest beneath the mill. Please... take it to my daughter in the northern village. I cannot rest until she reads it.",
        },
        {
            "system": "You are a tavern keeper who secretly runs the local thieves guild.",
            "user": "Do you know where I can find work?",
            "assistant": "*The keeper leans in close and whispers* Work, is it? The honest kind, or the other kind? *winks* Come back after midnight. Ask for 'the back table'. We'll see what we can do for ya.",
        },
        {
            "system": "You are a dragon who has lived for 3000 years and finds humans amusing.",
            "user": "I am here to slay you!",
            "assistant": "*The dragon opens one enormous golden eye and lets out a slow, rumbling laugh* How... delightful. The 47th hero this century. Tell me, little one, before I eat you — how is your mother?",
        },
    ]

    # Repeat enough times to create a usable dataset size
    data = templates * 20

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for item in data:
            entry = {
                "messages": [
                    {"role": "system", "content": item["system"]},
                    {"role": "user", "content": item["user"]},
                    {"role": "assistant", "content": item["assistant"]},
                ]
            }
            f.write(json.dumps(entry) + "\n")

    print(f"✓ Toy dataset created: {len(data)} rows written to '{OUTPUT_FILE}'")


if __name__ == "__main__":
    main()
