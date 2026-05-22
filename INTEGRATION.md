# Game Engine Integration Guide

This guide explains how to hook the NPC Engine into your game. We use **Unity (C#)** as the primary example, but the REST principles apply equally to Unreal Engine (C++) or Godot (GDScript).

## The "Drop-In" Unity Script

Inside this project, you will find a file named `Unity_NPC_Client.cs`. This script does all the heavy lifting.

### Step 1: Attach to GameObject
1. Create an NPC in your Unity Scene (e.g., a 3D model of an Orc).
2. Attach an `AudioSource` component to the Orc.
3. Drag and drop the `Unity_NPC_Client.cs` script onto the Orc.
4. Link the `AudioSource` component to the `npcAudioSource` slot in the script inspector.

### Step 2: Configure the Character
In the Unity Inspector for the `Unity_NPC_Client` script, fill out the character details:
* **Character Name**: `Grom`
* **Character Persona**: `An angry Orc blacksmith who hates humans.`
* **Voice Reference Wav**: `voices/grom.wav` (This must match a small audio file stored in your python server directory so the AI knows how to clone the voice).

### Step 3: Triggering the Conversation
From your player controller, whenever the player types a message or selects a dialogue option, simply call:
```csharp
gameObject.GetComponent<Unity_NPC_Client>().SpeakToNPC("Hello there, blacksmith!");
```

### Step 4: Hooking into Game Mechanics (The Magic)
Open `Unity_NPC_Client.cs` and look at the `TriggerGameEvent` function.

When the Python API responds, it includes a JSON tag called `trigger`. If the player says "Here is 50 gold, make me a sword", the AI might output `"trigger": "give_sword"`.

You can catch this in Unity:
```csharp
private void TriggerGameEvent(string eventName) {
    if (eventName == "give_sword") {
        PlayerInventory.AddItem("Iron Sword");
        QuestManager.CompleteQuest("Talk to Blacksmith");
    }
}
```

Likewise, the script logs the `emotion` tag (e.g., `angry`). You can hook this into your Unity Animator:
```csharp
myAnimator.SetTrigger(response.emotion); // Plays the "angry" facial animation!
```
