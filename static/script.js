const API_URL = window.location.origin;

// DOM Elements
const chatHistory = document.getElementById('chat-history');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.querySelector('.send-btn');
const statusDot = document.querySelector('.status-dot');
const serverStatusTxt = document.getElementById('server-status');
const audioPlayer = document.getElementById('audio-player');

const charNameInput = document.getElementById('char-name');
const charPersonaInput = document.getElementById('char-persona');
const sessionIdInput = document.getElementById('session-id');
const btnClearMem = document.getElementById('btn-clear-mem');

const worldForm = document.getElementById('world-form');
const gossipForm = document.getElementById('gossip-form');

// State
let isWaiting = false;

// Initialize
async function checkHealth() {
    try {
        const res = await fetch(`${API_URL}/health`);
        if (res.ok) {
            const data = await res.json();
            statusDot.className = 'status-dot online';
            serverStatusTxt.innerHTML = `<span class="status-dot online"></span> API Online (LLM: ${data.llm_loaded ? 'Yes' : 'No'})`;
        } else {
            setOffline();
        }
    } catch (e) {
        setOffline();
    }
}

function setOffline() {
    statusDot.className = 'status-dot offline';
    serverStatusTxt.innerHTML = `<span class="status-dot offline"></span> API Offline`;
}

// Check health every 10s
checkHealth();
setInterval(checkHealth, 10000);

// Fetch Initial World State
async function fetchWorldState() {
    try {
        const res = await fetch(`${API_URL}/world`);
        if (res.ok) {
            const state = await res.json();
            if (state.time_of_day) document.getElementById('world-time').value = state.time_of_day;
            if (state.weather) document.getElementById('world-weather').value = state.weather;
            if (state.current_region) document.getElementById('world-region').value = state.current_region;
            if (state.nearby_events) document.getElementById('world-events').value = state.nearby_events.join(", ");
        }
    } catch(e) {}
}
fetchWorldState();

// Chat UI functions
function appendUserMessage(text) {
    const div = document.createElement('div');
    div.className = 'message user-msg';
    div.textContent = text;
    chatHistory.appendChild(div);
    scrollToBottom();
}

function appendNpcMessage(charName, emotion, text, trigger) {
    const div = document.createElement('div');
    div.className = 'message npc-msg';
    
    let triggerHtml = '';
    if (trigger && trigger !== 'none') {
        triggerHtml = `<div class="trigger-tag">⚡ Event Triggered: ${trigger}</div>`;
    }

    div.innerHTML = `
        <div class="msg-header">
            <span>${charName}</span>
            <span class="emotion-tag">${emotion.toUpperCase()}</span>
        </div>
        <div class="msg-content">${text}</div>
        ${triggerHtml}
    `;
    chatHistory.appendChild(div);
    scrollToBottom();
}

function appendSystemMessage(text) {
    const div = document.createElement('div');
    div.className = 'message system-msg';
    div.textContent = text;
    chatHistory.appendChild(div);
    scrollToBottom();
}

function showTyping() {
    const div = document.createElement('div');
    div.className = 'typing-indicator';
    div.id = 'typing-indicator';
    div.innerHTML = '<span></span><span></span><span></span>';
    chatHistory.appendChild(div);
    scrollToBottom();
}

function removeTyping() {
    const typing = document.getElementById('typing-indicator');
    if (typing) typing.remove();
}

function scrollToBottom() {
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// Chat Submit
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (isWaiting) return;

    const text = chatInput.value.trim();
    if (!text) return;

    appendUserMessage(text);
    chatInput.value = '';
    
    isWaiting = true;
    sendBtn.disabled = true;
    showTyping();

    const payload = {
        session_id: sessionIdInput.value.trim() || 'player_001',
        character_name: charNameInput.value.trim() || 'Grom',
        character_persona: charPersonaInput.value.trim() || 'An angry Orc.',
        player_message: text,
        npc_location: document.getElementById('world-region').value.trim() || null
    };

    try {
        const res = await fetch(`${API_URL}/talk`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        removeTyping();

        if (res.ok) {
            const data = await res.json();
            appendNpcMessage(data.character, data.emotion, data.dialogue, data.trigger);
            
            if (data.audio_file) {
                audioPlayer.src = `${API_URL}/audio/${data.audio_file}`;
                audioPlayer.play().catch(e => console.log('Audio autoplay blocked', e));
            }
        } else {
            const err = await res.json();
            appendSystemMessage(`Error: ${err.detail || res.statusText}`);
        }
    } catch (err) {
        removeTyping();
        appendSystemMessage('Error: Cannot connect to server.');
    } finally {
        isWaiting = false;
        sendBtn.disabled = false;
        chatInput.focus();
    }
});

// Clear Memory
btnClearMem.addEventListener('click', async () => {
    const session = sessionIdInput.value.trim();
    const npc = charNameInput.value.trim();
    if (!session || !npc) return;

    try {
        await fetch(`${API_URL}/session/${session}/${npc}`, { method: 'DELETE' });
        appendSystemMessage(`Memory cleared for ${npc} (Session: ${session})`);
    } catch(e) {
        appendSystemMessage('Failed to clear memory.');
    }
});

// World Form Submit
worldForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const eventsVal = document.getElementById('world-events').value.trim();
    const eventsArr = eventsVal ? eventsVal.split(',').map(s => s.trim()) : [];

    const payload = {
        time_of_day: document.getElementById('world-time').value || null,
        weather: document.getElementById('world-weather').value || null,
        current_region: document.getElementById('world-region').value || null,
        nearby_events: eventsArr.length > 0 ? eventsArr : null
    };

    try {
        const res = await fetch(`${API_URL}/world`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if(res.ok) {
            const btn = worldForm.querySelector('button');
            const oldText = btn.textContent;
            btn.textContent = 'Updated!';
            btn.style.background = 'var(--success)';
            setTimeout(() => {
                btn.textContent = oldText;
                btn.style.background = '';
            }, 2000);
        }
    } catch(e) {}
});

// Gossip Form Submit
gossipForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const statusDiv = document.getElementById('gossip-status');
    
    const payload = {
        source_npc: document.getElementById('gossip-source').value.trim(),
        player_session_id: sessionIdInput.value.trim(),
        event_description: document.getElementById('gossip-event').value.trim(),
        sentiment: document.getElementById('gossip-sentiment').value
    };

    try {
        const res = await fetch(`${API_URL}/gossip`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (res.ok) {
            const data = await res.json();
            statusDiv.textContent = `Rumor spread to ${data.spread_to.length} NPCs!`;
            statusDiv.style.color = 'var(--success)';
            document.getElementById('gossip-event').value = '';
        } else {
            statusDiv.textContent = 'Error spreading rumor.';
            statusDiv.style.color = 'var(--danger)';
        }
    } catch(e) {
        statusDiv.textContent = 'Connection error.';
        statusDiv.style.color = 'var(--danger)';
    }
    setTimeout(() => { statusDiv.textContent = ''; }, 3000);
});
