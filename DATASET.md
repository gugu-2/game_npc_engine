# Dataset Documentation: The Roleplay Engine

To train an NPC that feels alive, you cannot use a standard Q&A dataset (like Wikipedia). If you train an NPC on Wikipedia, it will talk like a robot. 

To achieve the "Game Changer" level of immersion, we use a specialized, high-quality conversational roleplay dataset.

## 1. The Chosen Dataset
**Source:** `jondurbin/airoboros-3.2` (Hugging Face)
**Category Subset:** We strictly filter this dataset to only download the `"roleplay"` category.

### Why this dataset?
The Airoboros Roleplay dataset is widely considered one of the highest-quality, multi-turn conversational datasets available to the open-source community. 
- **High Quality:** The responses are incredibly descriptive, often mixing dialogue with physical actions (e.g., `*Grom slams his fist on the anvil* "I said no!"`). This is exactly what we want for game NPCs so we can extract those actions into game engine triggers!
- **Good Size:** The script pulls the *entire* roleplay category from the massive 58,000+ row dataset. This provides thousands of rich, highly detailed interactions, ensuring the LLM has a massive pool of character tropes to learn from without overfitting.

## 2. File Types and Formatting

### The Raw Source (Parquet)
Hugging Face stores the raw dataset as a `.parquet` file. This is a highly compressed, columnar storage format used in big data. Our `prepare_data.py` script automatically downloads and unzips this Parquet file into memory.

### The Training Format (JSONL)
Game Engines and Unsloth require data to be formatted in a very specific way. Our script transforms the Parquet data into a local **JSON Lines (`.jsonl`)** file named `npc_training_data.jsonl`.

In a `.jsonl` file, every single line is an independent, valid JSON object. We format each line into the standard "Gemma Chat Format":

```json
{
  "messages": [
    {"role": "system", "content": "You are Elara, an elven healer. You speak softly and use archaic words."},
    {"role": "user", "content": "I am bleeding badly, can you help?"},
    {"role": "assistant", "content": "*Elara rushes over, her eyes wide with concern.* 'Hush now, traveler. Drink this potion of moondust.'"}
  ]
}
```

## 3. How the Model Trains on This Data
During training (`train_npc.py`), the Unsloth engine reads the `.jsonl` file line by line. 
1. **The System Prompt (`"role": "system"`):** The AI learns that its entire personality is dictated by the System Prompt.
2. **The Assistant Response (`"role": "assistant"`):** The AI calculates the mathematical difference (loss) between its own generated text and the high-quality text in the dataset. 
3. Over thousands of rows, the Gemma-2 2B model rewires its neural weights (via LoRA adapters) to completely suppress its "helpful AI assistant" persona, and permanently adopt the "descriptive RPG character" persona.
