const socket = io();

let currentAvatar = '😃';
let currentRoomCode = null;
let mySid = null;
let currentGameState = null;
let pendingWildCardId = null;
let isSoundMuted = false;
let currentTutorialSlide = 1;

socket.on('connect', () => {
    mySid = socket.id;
    console.log("Connected to server! Socket ID:", mySid);
});

socket.on('error_message', (data) => {
    alert(data.message);
});

// Avatar selection
function selectAvatar(element, avatar) {
    document.querySelectorAll('.avatar-option').forEach(el => el.classList.remove('selected'));
    element.classList.add('selected');
    currentAvatar = avatar;
}

// Menu Navigation
function showPlayerSelectionScreen() {
    document.getElementById('main-menu-card').style.display = 'none';
    document.getElementById('player-count-screen').style.display = 'block';
    document.getElementById('online-lobby-screen').style.display = 'none';
}

function showOnlineLobbyScreen() {
    document.getElementById('main-menu-card').style.display = 'none';
    document.getElementById('player-count-screen').style.display = 'none';
    document.getElementById('online-lobby-screen').style.display = 'block';
}

function backToMainMenu() {
    document.getElementById('main-menu-card').style.display = 'block';
    document.getElementById('player-count-screen').style.display = 'none';
    document.getElementById('online-lobby-screen').style.display = 'none';
    document.getElementById('room-waiting').style.display = 'none';
}

// Quick Bot Match (2, 3, 4 Players - Image 2)
function startQuickBotMatch(playerCount) {
    unoAudio.init();
    const username = document.getElementById('username-input').value.trim() || 'Player';
    socket.emit('quick_bot_game', { username: username, avatar: currentAvatar, player_count: playerCount });
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
    document.getElementById('room-waiting').style.display = 'block';
    document.getElementById('online-lobby-screen').style.display = 'none';
});

socket.on('room_joined', (data) => {
    currentRoomCode = data.room_code;
    document.getElementById('display-room-code').innerText = currentRoomCode;
    document.getElementById('room-waiting').style.display = 'block';
    document.getElementById('online-lobby-screen').style.display = 'none';
    document.getElementById('player-count-screen').style.display = 'none';
    document.getElementById('main-menu-card').style.display = 'none';
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

// Sound & Fullscreen Toggles
function toggleSound() {
    isSoundMuted = !isSoundMuted;
    const btn = document.getElementById('sound-btn');
    if (isSoundMuted) {
        btn.innerText = '🔇';
        unoAudio.soundEnabled = false;
    } else {
        btn.innerText = '🔊';
        unoAudio.soundEnabled = true;
    }
}

function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(err => console.log(err));
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        }
    }
}

// Tutorial Modal (Images 3, 4, 5)
function openTutorial() {
    currentTutorialSlide = 1;
    updateTutorialSlideDisplay();
    document.getElementById('tutorial-modal').style.display = 'flex';
}

function closeTutorial() {
    document.getElementById('tutorial-modal').style.display = 'none';
}

function nextTutorialSlide() {
    if (currentTutorialSlide < 3) {
        currentTutorialSlide++;
        updateTutorialSlideDisplay();
    }
}

function prevTutorialSlide() {
    if (currentTutorialSlide > 1) {
        currentTutorialSlide--;
        updateTutorialSlideDisplay();
    }
}

function updateTutorialSlideDisplay() {
    for (let i = 1; i <= 3; i++) {
        document.getElementById(`t-slide-${i}`).style.display = (i === currentTutorialSlide) ? 'flex' : 'none';
    }
    document.getElementById('slide-indicator').innerText = `${currentTutorialSlide} / 3`;
}

// Render game state
socket.on('game_state', (state) => {
    currentGameState = state;

    if (state.status === 'lobby') {
        document.getElementById('lobby-screen').style.display = 'flex';
        document.getElementById('game-screen').style.display = 'none';

        const playersList = document.getElementById('players-list');
        playersList.innerHTML = '';
        document.getElementById('player-count').innerText = state.players.length;

        state.players.forEach(p => {
            const slot = document.createElement('div');
            slot.style.cssText = 'background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255,255,255,0.15); border-radius: 14px; padding: 15px; text-align: center;';
            slot.innerHTML = `
                <div style="font-size: 2.2rem; margin-bottom: 5px;">${p.avatar}</div>
                <div style="font-weight: bold; font-size: 0.9rem;">${p.name}</div>
            `;
            playersList.appendChild(slot);
        });

    } else if (state.status === 'playing' || state.status === 'finished') {
        document.getElementById('lobby-screen').style.display = 'none';
        document.getElementById('game-screen').style.display = 'flex';

        renderGameTable(state);

        if (state.status === 'finished' && state.winner) {
            showVictoryModal(state.winner, state.last_round_points);
        }
    }
});

function renderGameTable(state) {
    const opponentsBar = document.getElementById('opponents-bar');
    opponentsBar.innerHTML = '';

    const me = state.players.find(p => p.sid === mySid);

    state.players.forEach(p => {
        if (p.sid !== mySid) {
            const card = document.createElement('div');
            card.className = `opponent-card ${p.is_current ? 'turn-active' : ''}`;
            card.innerHTML = `
                <span style="font-size: 1.6rem;">${p.avatar}</span>
                <div>
                    <div style="font-weight: bold; font-size: 0.85rem;">${p.name} ${p.called_uno ? '🔥 UNO!' : ''}</div>
                    <div style="display: flex; gap: 6px; margin-top: 2px;">
                        <span class="hand-badge">🃏 ${p.hand_count}</span>
                        <span class="score-badge">🏆 ${p.score} PTS</span>
                    </div>
                </div>
            `;
            if (p.hand_count === 1 && !p.called_uno) {
                card.style.cursor = 'pointer';
                card.title = 'Click to catch UNO failure!';
                card.onclick = () => socket.emit('catch_uno', { target_sid: p.sid });
            }
            opponentsBar.appendChild(card);
        }
    });

    const ring = document.getElementById('direction-ring');
    if (state.direction === -1) {
        ring.classList.add('counter-clockwise');
    } else {
        ring.classList.remove('counter-clockwise');
    }

    const colorBanner = document.getElementById('current-color-banner');
    colorBanner.className = `color-banner ${state.current_color || 'red'}`;
    document.getElementById('color-name').innerText = (state.current_color || 'RED').toUpperCase();

    const discardContainer = document.getElementById('discard-pile-container');
    discardContainer.innerHTML = '';
    if (state.top_discard) {
        discardContainer.appendChild(createCardElement(state.top_discard, false));
    }

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

// Create Arcade Styled Cards (Images 1, 3, 4, 5)
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
        <div class="card-corner top-left">${valDisplay}</div>
        <div class="card-diamond-badge">
            <span class="card-diamond-inner">${valDisplay}</span>
        </div>
        <div class="card-corner bottom-right">${valDisplay}</div>
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
        if (!isSoundMuted) unoAudio.playCardSound();
    }
}

function selectWildColor(color) {
    document.getElementById('color-modal').style.display = 'none';
    if (pendingWildCardId) {
        socket.emit('play_card', { card_id: pendingWildCardId, chosen_color: color });
        if (!isSoundMuted) unoAudio.playCardSound();
        pendingWildCardId = null;
    }
}

function drawCard() {
    if (!currentGameState || currentGameState.current_player_sid !== mySid) {
        alert("It's not your turn!");
        return;
    }
    socket.emit('draw_card', {});
    if (!isSoundMuted) unoAudio.playDrawSound();
}

function callUno() {
    socket.emit('call_uno', {});
    if (!isSoundMuted) unoAudio.playUnoShoutSound();
}

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
    if (!isSoundMuted) unoAudio.playUnoShoutSound();
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

function showVictoryModal(winner, pointsWon) {
    if (!isSoundMuted) unoAudio.playVictorySound();
    document.getElementById('winner-desc').innerText = `${winner.avatar} ${winner.name} won the round!`;
    document.getElementById('winner-score-info').innerText = `+${pointsWon} PTS Earned! Total: ${winner.score} / 250 PTS`;
    document.getElementById('victory-modal').style.display = 'flex';
}

function closeVictoryModal() {
    document.getElementById('victory-modal').style.display = 'none';
}
