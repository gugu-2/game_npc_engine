using System;
using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

[System.Serializable]
public class NPCResponse
{
    public string character;
    public string dialogue;
    public string emotion;
    public string trigger;
    public string audio_file;
}

/// <summary>
/// Drop-in Unity component for the Ultimate Game NPC Engine.
/// Attach to any NPC GameObject. Assign an AudioSource and call SpeakToNPC() from your dialogue UI.
/// </summary>
public class Unity_NPC_Client : MonoBehaviour
{
    [Header("Server Settings")]
    public string apiUrl      = "http://localhost:8000/talk";
    public string audioApiUrl = "http://localhost:8000/audio/";
    public string healthUrl   = "http://localhost:8000/health";

    [Header("NPC Identity")]
    public string sessionID        = "";          // Leave blank to auto-generate on Start()
    public string characterName    = "Grom";
    [TextArea(2, 5)]
    public string characterPersona = "An angry Orc blacksmith who hates humans.";

    [Header("Voice")]
    public string voiceReferenceWav = "voices/grom.wav";

    [Header("Components")]
    public AudioSource npcAudioSource;

    // BUG FIX: Exposed events so other Unity scripts can react to AI responses
    // without modifying this script (clean Observer pattern).
    public event Action<string>     OnDialogueReceived;
    public event Action<string>     OnEmotionChanged;
    public event Action<string>     OnQuestTriggered;

    // BUG FIX: Prevent the player from spamming the NPC while a response is in-flight
    private bool _isWaiting = false;

    private void Start()
    {
        // BUG FIX: Auto-generate a unique session ID if the developer left it blank.
        // This prevents all NPCs of the same type sharing the same conversation memory.
        if (string.IsNullOrEmpty(sessionID))
        {
            sessionID = $"{characterName}_{gameObject.GetInstanceID()}_{Guid.NewGuid().ToString("N").Substring(0, 8)}";
        }

        // Validate that an AudioSource is assigned
        if (npcAudioSource == null)
        {
            npcAudioSource = GetComponent<AudioSource>();
            if (npcAudioSource == null)
                Debug.LogWarning($"[{characterName}] No AudioSource assigned. Voice will not play.");
        }
    }

    public void SpeakToNPC(string playerMessage)
    {
        if (_isWaiting)
        {
            Debug.Log($"[{characterName}] Still processing previous message. Please wait.");
            return;
        }
        if (string.IsNullOrWhiteSpace(playerMessage)) return;

        StartCoroutine(SendChatRequest(playerMessage));
    }

    /// <summary>Call this when a scene changes or the NPC is reset to clear server-side memory.</summary>
    public void ClearMemory()
    {
        StartCoroutine(DeleteSession());
    }

    private IEnumerator DeleteSession()
    {
        string url = $"http://localhost:8000/session/{sessionID}/{characterName}";
        using (UnityWebRequest www = UnityWebRequest.Delete(url))
        {
            yield return www.SendWebRequest();
            if (www.result == UnityWebRequest.Result.Success)
                Debug.Log($"[{characterName}] Session memory cleared on server.");
        }
    }

    private IEnumerator SendChatRequest(string message)
    {
        _isWaiting = true;

        // BUG FIX: Old code built JSON by string interpolation which breaks
        // if the player's message contains quotes. We now use a proper serializable
        // class and JsonUtility to guarantee safe JSON encoding.
        var requestData = new NPCChatRequest
        {
            session_id          = sessionID,
            character_name      = characterName,
            character_persona   = characterPersona,
            player_message      = message,
            voice_reference_wav = voiceReferenceWav
        };
        string jsonPayload = JsonUtility.ToJson(requestData);

        using (UnityWebRequest request = new UnityWebRequest(apiUrl, "POST"))
        {
            byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonPayload);
            request.uploadHandler   = new UploadHandlerRaw(bodyRaw);
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");
            request.timeout = 60; // BUG FIX: Add timeout so the game doesn't freeze if the server dies

            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                NPCResponse response = JsonUtility.FromJson<NPCResponse>(request.downloadHandler.text);

                Debug.Log($"[{response.character}] [{response.emotion.ToUpper()}]: {response.dialogue}");

                // Fire events for other systems to consume
                OnDialogueReceived?.Invoke(response.dialogue);
                OnEmotionChanged?.Invoke(response.emotion);

                if (!string.IsNullOrEmpty(response.trigger) && response.trigger != "none")
                {
                    Debug.Log($"[NPC ENGINE] Quest trigger received: {response.trigger}");
                    OnQuestTriggered?.Invoke(response.trigger);
                    TriggerGameEvent(response.trigger);
                }

                if (!string.IsNullOrEmpty(response.audio_file))
                {
                    StartCoroutine(PlayAudio(response.audio_file));
                }
            }
            else
            {
                Debug.LogError($"[{characterName}] API Error ({request.responseCode}): {request.error}");
            }
        }

        _isWaiting = false;
    }

    private IEnumerator PlayAudio(string filename)
    {
        // BUG FIX: Old code passed the full audio_file path returned by the server,
        // but the /audio/ endpoint expects only the base filename.
        string justFilename = System.IO.Path.GetFileName(filename);
        string url = audioApiUrl + justFilename;

        using (UnityWebRequest www = UnityWebRequestMultimedia.GetAudioClip(url, AudioType.WAV))
        {
            yield return www.SendWebRequest();

            if (www.result == UnityWebRequest.Result.Success)
            {
                AudioClip clip = DownloadHandlerAudioClip.GetContent(www);
                if (npcAudioSource != null)
                {
                    npcAudioSource.clip = clip;
                    npcAudioSource.Play();
                }
            }
            else
            {
                Debug.LogWarning($"[{characterName}] Could not fetch audio: {www.error}");
            }
        }
    }

    /// <summary>Override or extend this method to wire up your game's quest/event system.</summary>
    protected virtual void TriggerGameEvent(string eventName)
    {
        Debug.Log($"[GAME EVENT] '{eventName}' — handle this in your game's event system.");
        // Example:
        // if (eventName == "give_sword") PlayerInventory.Instance.AddItem("Iron Sword");
        // if (eventName == "open_gate")  GateController.Instance.Open();
    }
}

// BUG FIX: Separate serializable class for the request body to ensure correct JSON encoding
[System.Serializable]
internal class NPCChatRequest
{
    public string session_id;
    public string character_name;
    public string character_persona;
    public string player_message;
    public string voice_reference_wav;
}
