## NPC Engine — Godot 4 GDScript SDK
## File: NPCEngineClient.gd
## Attach to any NPC Node in your Godot scene.

extends Node

# ─────────────────────────────────────────────────────────────
# Signals (equivalent to Unity events / Unreal delegates)
# ─────────────────────────────────────────────────────────────
signal dialogue_received(character: String, dialogue: String, emotion: String)
signal quest_triggered(trigger_name: String)
signal error_occurred(message: String)

# ─────────────────────────────────────────────────────────────
# Inspector-editable properties
# ─────────────────────────────────────────────────────────────
@export var server_url: String = "http://localhost:8000"
@export var session_id: String = ""          # Auto-generated if empty
@export var character_name: String = "NPC"
@export_multiline var character_persona: String = "A wise village elder."
@export var voice_reference_wav: String = "" # Leave empty for emotion-auto-select
@export var npc_audio_player: AudioStreamPlayer = null

var _is_waiting: bool = false
var _http: HTTPRequest

# ─────────────────────────────────────────────────────────────
func _ready():
    # Auto-generate a unique session ID
    if session_id.is_empty():
        session_id = "%s_%s" % [character_name, str(randi()).left(8)]

    _http = HTTPRequest.new()
    add_child(_http)
    _http.request_completed.connect(_on_talk_response)
    print("[NPCEngine] %s ready. Session: %s" % [character_name, session_id])

# ─────────────────────────────────────────────────────────────
func speak_to_npc(player_message: String) -> void:
    if _is_waiting:
        push_warning("[NPCEngine] %s is still processing." % character_name)
        return
    if player_message.strip_edges().is_empty():
        return

    _is_waiting = true

    var payload = {
        "session_id": session_id,
        "character_name": character_name,
        "character_persona": character_persona,
        "player_message": player_message,
        "voice_reference_wav": voice_reference_wav if not voice_reference_wav.is_empty() else null
    }

    var json_str = JSON.stringify(payload)
    var headers = ["Content-Type: application/json"]

    var err = _http.request(server_url + "/talk", headers, HTTPClient.METHOD_POST, json_str)
    if err != OK:
        _is_waiting = false
        error_occurred.emit("Failed to send request: %s" % err)

func _on_talk_response(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
    _is_waiting = false

    if result != HTTPRequest.RESULT_SUCCESS:
        error_occurred.emit("Connection to NPC Engine failed.")
        return

    if response_code != 200:
        error_occurred.emit("Server returned HTTP %d" % response_code)
        return

    var json = JSON.new()
    if json.parse(body.get_string_from_utf8()) != OK:
        error_occurred.emit("Failed to parse server response.")
        return

    var data = json.get_data()
    var character = data.get("character", character_name)
    var dialogue  = data.get("dialogue",  "...")
    var emotion   = data.get("emotion",   "neutral")
    var trigger   = data.get("trigger",   "none")
    var audio_file = data.get("audio_file", "")

    print("[%s][%s]: %s" % [character, emotion.to_upper(), dialogue])

    dialogue_received.emit(character, dialogue, emotion)

    if trigger != "none" and not trigger.is_empty():
        print("[NPCEngine] Quest trigger: %s" % trigger)
        quest_triggered.emit(trigger)

    if not audio_file.is_empty():
        _download_audio(audio_file.get_file())

# ─────────────────────────────────────────────────────────────
func _download_audio(filename: String) -> void:
    var audio_http = HTTPRequest.new()
    add_child(audio_http)
    audio_http.request_completed.connect(func(r, code, h, body):
        if code == 200:
            var stream = AudioStreamWAV.new()
            stream.data = body
            if npc_audio_player:
                npc_audio_player.stream = stream
                npc_audio_player.play()
        audio_http.queue_free()
    )
    audio_http.request(server_url + "/audio/" + filename)

# ─────────────────────────────────────────────────────────────
func clear_memory() -> void:
    var http = HTTPRequest.new()
    add_child(http)
    http.request_completed.connect(func(r, c, h, b): http.queue_free())
    http.request(server_url + "/session/%s/%s" % [session_id, character_name],
                 [], HTTPClient.METHOD_DELETE)

func report_gossip(event_description: String, gossip_speed: float = 0.7) -> void:
    var payload = JSON.stringify({
        "source_npc": character_name,
        "player_session_id": session_id,
        "event_description": event_description,
        "gossip_speed": gossip_speed
    })
    var http = HTTPRequest.new()
    add_child(http)
    http.request_completed.connect(func(r, c, h, b): http.queue_free())
    http.request(server_url + "/gossip", ["Content-Type: application/json"],
                 HTTPClient.METHOD_POST, payload)

func update_world_state(state: Dictionary) -> void:
    var payload = JSON.stringify(state)
    var http = HTTPRequest.new()
    add_child(http)
    http.request_completed.connect(func(r, c, h, b): http.queue_free())
    http.request(server_url + "/world", ["Content-Type: application/json"],
                 HTTPClient.METHOD_PUT, payload)
