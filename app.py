import os
import random
import string
import time
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from dotenv import load_dotenv

from database import get_or_create_user, update_user_stats, get_leaderboard, save_game_history
from uno_logic import UnoGame

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "uno-secret-key-2026")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

games = {} # room_code -> UnoGame
user_sessions = {} # sid -> {username, avatar, room_code}

def generate_room_code():
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if code not in games:
            return code

def broadcast_game_state(room_code):
    if room_code not in games:
        return
    game = games[room_code]
    for p in game.players:
        if not p['is_bot']:
            socketio.emit('game_state', game.to_dict(for_sid=p['sid']), to=p['sid'])

def trigger_bot_turns_if_needed(room_code):
    if room_code not in games:
        return
    game = games[room_code]
    if game.status != 'playing':
        return

    curr_p = game.get_current_player()
    if curr_p and curr_p['is_bot']:
        socketio.sleep(1.2) # Natural delay for bot turn
        if room_code in games and game.status == 'playing':
            game.bot_take_turn()
            broadcast_game_state(room_code)
            
            if game.status == 'finished':
                _handle_game_finished(game)
            else:
                trigger_bot_turns_if_needed(room_code)

def _handle_game_finished(game):
    winner_name = game.winner['name'] if game.winner else "Unknown"
    for p in game.players:
        if not p['is_bot']:
            is_win = (game.winner and p['sid'] == game.winner['sid'])
            update_user_stats(p['name'], won=is_win, cards_played=p['cards_played_count'])
            
    player_names = [p['name'] for p in game.players]
    save_game_history(game.room_code, winner_name, game.turn_count, player_names)
    broadcast_game_state(game.room_code)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/leaderboard')
def api_leaderboard():
    lb = get_leaderboard()
    return jsonify(lb)

@socketio.on('connect')
def handle_connect():
    pass

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in user_sessions:
        session = user_sessions[sid]
        room_code = session.get('room_code')
        if room_code in games:
            game = games[room_code]
            game.remove_player(sid)
            leave_room(room_code)
            if len([p for p in game.players if not p['is_bot']]) == 0:
                # Cleanup empty rooms after disconnects
                del games[room_code]
            else:
                broadcast_game_state(room_code)
        del user_sessions[sid]

@socketio.on('create_room')
def handle_create_room(data):
    username = data.get('username', 'Player').strip()
    avatar = data.get('avatar', '😃')
    
    get_or_create_user(username, avatar)
    room_code = generate_room_code()
    game = UnoGame(room_code)
    games[room_code] = game
    
    player = game.add_player(request.sid, username, avatar)
    user_sessions[request.sid] = {'username': username, 'avatar': avatar, 'room_code': room_code}
    join_room(room_code)
    
    emit('room_created', {'room_code': room_code, 'player': player})
    broadcast_game_state(room_code)

@socketio.on('join_room')
def handle_join_room(data):
    room_code = data.get('room_code', '').upper().strip()
    username = data.get('username', 'Player').strip()
    avatar = data.get('avatar', '😃')
    
    if room_code not in games:
        emit('error_message', {'message': 'Room code not found!'})
        return
        
    game = games[room_code]
    if len(game.players) >= 6:
        emit('error_message', {'message': 'Room is full (max 6 players)!'})
        return
        
    if game.status == 'playing':
        emit('error_message', {'message': 'Game already in progress!'})
        return
        
    get_or_create_user(username, avatar)
    player = game.add_player(request.sid, username, avatar)
    user_sessions[request.sid] = {'username': username, 'avatar': avatar, 'room_code': room_code}
    join_room(room_code)
    
    emit('room_joined', {'room_code': room_code, 'player': player})
    broadcast_game_state(room_code)

@socketio.on('add_bot')
def handle_add_bot(data):
    sid = request.sid
    if sid not in user_sessions:
        return
    room_code = user_sessions[sid]['room_code']
    if room_code in games:
        game = games[room_code]
        if len(game.players) < 6 and game.status == 'lobby':
            bot = game.add_bot()
            broadcast_game_state(room_code)

@socketio.on('start_game')
def handle_start_game():
    sid = request.sid
    if sid not in user_sessions:
        return
    room_code = user_sessions[sid]['room_code']
    if room_code in games:
        game = games[room_code]
        success, msg = game.start_game()
        if not success:
            emit('error_message', {'message': msg})
        else:
            broadcast_game_state(room_code)
            socketio.start_background_task(trigger_bot_turns_if_needed, room_code)

@socketio.on('play_card')
def handle_play_card(data):
    sid = request.sid
    if sid not in user_sessions:
        return
    room_code = user_sessions[sid]['room_code']
    if room_code in games:
        game = games[room_code]
        card_id = data.get('card_id')
        chosen_color = data.get('chosen_color')
        
        success, msg = game.play_card(sid, card_id, chosen_color)
        if not success:
            emit('error_message', {'message': msg})
        else:
            broadcast_game_state(room_code)
            if game.status == 'finished':
                _handle_game_finished(game)
            else:
                socketio.start_background_task(trigger_bot_turns_if_needed, room_code)

@socketio.on('draw_card')
def handle_draw_card():
    sid = request.sid
    if sid not in user_sessions:
        return
    room_code = user_sessions[sid]['room_code']
    if room_code in games:
        game = games[room_code]
        success, msg, card = game.player_draw_card(sid)
        if not success:
            emit('error_message', {'message': msg})
        else:
            broadcast_game_state(room_code)
            socketio.start_background_task(trigger_bot_turns_if_needed, room_code)

@socketio.on('call_uno')
def handle_call_uno():
    sid = request.sid
    if sid not in user_sessions:
        return
    room_code = user_sessions[sid]['room_code']
    if room_code in games:
        game = games[room_code]
        success, msg = game.call_uno(sid)
        if not success:
            emit('error_message', {'message': msg})
        else:
            socketio.emit('uno_shout', {'player_name': user_sessions[sid]['username']}, to=room_code)
            broadcast_game_state(room_code)

@socketio.on('catch_uno')
def handle_catch_uno(data):
    sid = request.sid
    target_sid = data.get('target_sid')
    if sid not in user_sessions:
        return
    room_code = user_sessions[sid]['room_code']
    if room_code in games:
        game = games[room_code]
        success, msg = game.catch_uno_failure(sid, target_sid)
        emit('error_message', {'message': msg})
        broadcast_game_state(room_code)

@socketio.on('send_chat')
def handle_send_chat(data):
    sid = request.sid
    if sid not in user_sessions:
        return
    room_code = user_sessions[sid]['room_code']
    msg = data.get('message', '').strip()
    if msg:
        username = user_sessions[sid]['username']
        avatar = user_sessions[sid]['avatar']
        socketio.emit('new_chat', {
            'username': username,
            'avatar': avatar,
            'message': msg,
            'time': time.strftime("%H:%M")
        }, to=room_code)

@socketio.on('send_emoji')
def handle_send_emoji(data):
    sid = request.sid
    if sid not in user_sessions:
        return
    room_code = user_sessions[sid]['room_code']
    emoji_char = data.get('emoji', '🔥')
    username = user_sessions[sid]['username']
    socketio.emit('floating_emoji', {
        'emoji': emoji_char,
        'sender': username
    }, to=room_code)

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    print(f"🚀 UNO Game Server starting on http://localhost:{port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
