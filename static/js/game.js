const socket = io();

let currentAvatar = '😃';
let currentRoomCode = null;
let mySid = null;
let currentGameState = null;
let pendingWildCardId = null;

socket.on('connect', () => {
    mySid = socket.id;
    console.log("Connected to server! Socket ID:", mySid);
});

socket.on('error_message', (data) => {
    alert(data.message);
});

function selectAvatar(element, avatar) {
    document.querySelectorAll('.avatar-option').forEach(el => el.classList.remove('selected'));
    element.classList.add('selected');
    currentAvatar = avatar;
}

function handleJoinOrCreate() {
    unoAudio.init();
    const username = document.getElementById('username-input').value.trim() || 'Player';
    const roomCodeInput = document.getElementById('room-input').value.trim().toUpperCase();

    if (roomCodeInput) {
        socket.emit('join_room', { username: username, avatar: currentAvatar, room_code: roomCodeInput });
    } else {
        socket.emit('create_room', { username: username, avatar: currentAvatar });
    }
}

socket.on('room_created', (data) => {
    currentRoomCode = data.room_code;
    document.getElementById('display-room-code').innerText = currentRoomCode;
    document.getElementById('room-waiting').style.display = 'flex';
    document.querySelector('.lobby-card').style.display = 'none';
});

socket.on('room_joined', (data) => {
    currentRoomCode = data.room_code;
    document.getElementById('display-room-code').innerText = currentRoomCode;
    document.getElementById('room-waiting').style.display = 'flex';
    document.querySelector('.lobby-card').style.display = 'none';
});

function addBotPlayer() {
    socket.emit('add_bot', {});
}

function startGame() {
    socket.emit('start_game', {});
}

function copyRoomCode() {
    navigator.clipboard.writeText(currentRoomCode);
    alert("Room Code copied to clipboard: " + currentRoomCode);
}

// Render game state from server
socket.on('game_state', (state) => {
    currentGameState = state;

    if (state.status === 'lobby') {
        document.getElementById('lobby-screen').style.display = 'flex';
        document.getElementById('game-screen').style.display = 'none';

        // Update waiting players list
        const playersList = document.getElementById('players-list');
        playersList.innerHTML = '';
        document.getElementById('player-count').innerText = state.players.length;

        state.players.forEach(p => {
            const slot = document.createElement('div');
            slot.className = 'player-slot active';
            slot.innerHTML = `
                <div class="player-avatar">${p.avatar}</div>
                <div style="font-weight: bold; font-size: 0.9rem;">${p.name}</div>
            `;
            playersList.appendChild(slot);
        });

    } else if (state.status === 'playing' || state.status === 'finished') {
        document.getElementById('lobby-screen').style.display = 'none';
        document.getElementById('game-screen').style.display = 'flex';

        renderGameTable(state);

        if (state.status === 'finished' && state.winner) {
            showVictoryModal(state.winner);
        }
    }
});

function renderGameTable(state) {
    // Render opponents
    const opponentsBar = document.getElementById('opponents-bar');
    opponentsBar.innerHTML = '';

    const me = state.players.find(p => p.sid === mySid);

    state.players.forEach(p => {
        if (p.sid !== mySid) {
            const card = document.createElement('div');
            card.className = `opponent-card ${p.is_current ? 'turn-active' : ''}`;
            card.innerHTML = `
                <span style="font-size: 1.5rem;">${p.avatar}</span>
                <div>
                    <div style="font-weight: bold; font-size: 0.85rem;">${p.name} ${p.called_uno ? '🔥 UNO!' : ''}</div>
                    <span class="hand-badge">🃏 ${p.hand_count}</span>
                </div>
            `;
            // Click opponent to catch UNO failure if they have 1 card
            if (p.hand_count === 1 && !p.called_uno) {
                card.style.cursor = 'pointer';
                card.title = 'Click to catch UNO failure!';
                card.onclick = () => socket.emit('catch_uno', { target_sid: p.sid });
            }
            opponentsBar.appendChild(card);
        }
    });

    // Render Direction Ring
    const ring = document.getElementById('direction-ring');
    if (state.direction === -1) {
        ring.classList.add('counter-clockwise');
    } else {
        ring.classList.remove('counter-clockwise');
    }

    // Render Color Banner
    const colorBanner = document.getElementById('current-color-banner');
    colorBanner.className = `color-banner ${state.current_color || 'red'}`;
    document.getElementById('color-name').innerText = (state.current_color || 'RED').toUpperCase();

    // Render Discard Pile Top Card
    const discardContainer = document.getElementById('discard-pile-container');
    discardContainer.innerHTML = '';
    if (state.top_discard) {
        discardContainer.appendChild(createCardElement(state.top_discard, false));
    }

    // Render Player Hand
    const handContainer = document.getElementById('player-hand');
    handContainer.innerHTML = '';

    if (me && me.hand) {
        me.hand.forEach(c => {
            const cardEl = createCardElement(c, true);
            cardEl.onclick = () => onCardClicked(c);
            handContainer.appendChild(cardEl);
        });
    }

    document.getElementById('deck-count-tag').innerText = `Cards: ${state.deck_count}`;
}

function createCardElement(card, isInteractive) {
    const cardEl = document.createElement('div');
    cardEl.className = `uno-card ${card.color}`;

    let valDisplay = card.value.toUpperCase();
    if (card.value === 'skip') valDisplay = '🚫';
    else if (card.value === 'reverse') valDisplay = '🔄';
    else if (card.value === 'draw2') valDisplay = '+2';
    else if (card.value === 'wild') valDisplay = '🎨';
    else if (card.value === 'wild_draw4') valDisplay = '+4';

    cardEl.innerHTML = `
        <div class="uno-card-oval">
            <span class="uno-card-value">${valDisplay}</span>
        </div>
    `;

    return cardEl;
}

function onCardClicked(card) {
    if (!currentGameState || currentGameState.current_player_sid !== mySid) {
        alert("It's not your turn!");
        return;
    }

    if (card.color === 'wild' || card.type === 'wild' || card.type === 'wild_draw4') {
        pendingWildCardId = card.id;
        document.getElementById('color-modal').style.display = 'flex';
    } else {
        socket.emit('play_card', { card_id: card.id });
        unoAudio.playCardSound();
    }
}

function selectWildColor(color) {
    document.getElementById('color-modal').style.display = 'none';
    if (pendingWildCardId) {
        socket.emit('play_card', { card_id: pendingWildCardId, chosen_color: color });
        unoAudio.playCardSound();
        pendingWildCardId = null;
    }
}

function drawCard() {
    if (!currentGameState || currentGameState.current_player_sid !== mySid) {
        alert("It's not your turn!");
        return;
    }
    socket.emit('draw_card', {});
    unoAudio.playDrawSound();
}

function callUno() {
    socket.emit('call_uno', {});
    unoAudio.playUnoShoutSound();
}

// Floating Emoji Reaction System
function sendEmoji(emojiChar) {
    socket.emit('send_emoji', { emoji: emojiChar });
}

socket.on('floating_emoji', (data) => {
    spawnFloatingEmoji(data.emoji, data.sender);
});

function spawnFloatingEmoji(emojiChar, senderName) {
    const overlay = document.getElementById('emoji-overlay');
    const el = document.createElement('div');
    el.className = 'floating-emoji';
    el.innerText = emojiChar;

    const startX = Math.random() * (window.innerWidth - 100) + 50;
    el.style.left = `${startX}px`;
    el.style.bottom = '50px';

    overlay.appendChild(el);

    setTimeout(() => {
        if (el.parentNode) el.parentNode.removeChild(el);
    }, 2500);
}

// Live Chat Drawer & Messages
function toggleChat() {
    const drawer = document.getElementById('chat-drawer');
    drawer.classList.toggle('open');
}

function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (msg) {
        socket.emit('send_chat', { message: msg });
        input.value = '';
    }
}

socket.on('new_chat', (data) => {
    const container = document.getElementById('chat-messages');
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';
    bubble.innerHTML = `
        <div class="chat-author">${data.avatar} ${data.username} <span style="font-weight: normal; font-size: 0.75rem; color: #94a3b8;">${data.time}</span></div>
        <div>${data.message}</div>
    `;
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
});

socket.on('uno_shout', (data) => {
    spawnFloatingEmoji('🔥 UNO!', data.player_name);
    unoAudio.playUnoShoutSound();
});

// Leaderboard Modal
function openLeaderboard() {
    fetch('/api/leaderboard')
        .then(res => res.json())
        .then(data => {
            const list = document.getElementById('leaderboard-list');
            list.innerHTML = '';
            data.forEach((user, idx) => {
                const item = document.createElement('div');
                item.style.cssText = 'display: flex; justify-content: space-between; padding: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); background: rgba(15,23,42,0.4); border-radius: 10px; margin-bottom: 8px;';
                item.innerHTML = `
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <span style="font-weight: bold; width: 20px;">#${idx + 1}</span>
                        <span>${user.avatar} ${user.username}</span>
                    </div>
                    <div style="font-weight: bold; color: #60a5fa;">
                        🏆 ${user.wins} Wins | 🃏 ${user.cards_played} Cards
                    </div>
                `;
                list.appendChild(item);
            });
            document.getElementById('leaderboard-modal').style.display = 'flex';
        });
}

function closeLeaderboard() {
    document.getElementById('leaderboard-modal').style.display = 'none';
}

function showVictoryModal(winner) {
    unoAudio.playVictorySound();
    document.getElementById('winner-desc').innerText = `${winner.avatar} ${winner.name} won the match!`;
    document.getElementById('victory-modal').style.display = 'flex';
}

function closeVictoryModal() {
    document.getElementById('victory-modal').style.display = 'none';
}
