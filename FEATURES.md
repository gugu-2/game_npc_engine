# Ultimate Game NPC Engine: Features

## 1. Zero-Shot Voice Cloning (Coqui XTTS-v2)
**How it works:** Game developers don't need to train a voice model. They simply drop a 3-second `.wav` file into the folder (e.g., a recording of a voice actor acting angry, or a female elf voice). 
When the Unity game sends a request to the API, it passes the filename `"voice_reference_wav": "elf.wav"`. The engine instantly clones that voice and speaks the AI's dialogue using that exact tone and pitch!

## 2. In-Game Lore Awareness (RAG)
**How it works:** The engine reads `lore.json`. If a player talks to "Grom", the AI automatically pulls Grom's secrets from the JSON file and injects them into its brain before it speaks. The AI will never hallucinate game lore again.

## 3. Dynamic Quest Triggers
**How it works:** We forced the AI to output strictly formatted JSON. If the player convinces the NPC to do something, the AI outputs `"trigger": "give_quest_item"`. The `Unity_NPC_Client.cs` script catches this trigger and can execute C# code to actually spawn an item in the player's inventory!

## 4. Persistent Memory
**How it works:** The API tracks the `session_id`. The Unity developer doesn't have to send the entire chat history over the network every frame. They just send the player's current message, and the Python server remembers the rest.

## 5. Ultra-Fast Local Inference
**How it works:** By leveraging **Gemma-2 2B** quantized in 4-bit, the LLM consumes minimal GPU VRAM (leaving plenty of memory for the game engine to render 3D graphics). It provides near-instantaneous text generation so players aren't left waiting awkwardly for an NPC to respond.
