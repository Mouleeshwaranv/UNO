import random

COLORS = ['red', 'blue', 'green', 'yellow']
VALUES = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'skip', 'reverse', 'draw2']

def generate_deck():
    deck = []
    card_id = 1
    for color in COLORS:
        # One 0 card per color
        deck.append({'id': card_id, 'color': color, 'value': '0', 'type': 'number'})
        card_id += 1
        # Two of 1-9 per color
        for val in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
            for _ in range(2):
                deck.append({'id': card_id, 'color': color, 'value': val, 'type': 'number'})
                card_id += 1
        # Two of action cards per color
        for val in ['skip', 'reverse', 'draw2']:
            for _ in range(2):
                deck.append({'id': card_id, 'color': color, 'value': val, 'type': val})
                card_id += 1
    # Wild cards (4 Wild, 4 Wild Draw 4)
    for _ in range(4):
        deck.append({'id': card_id, 'color': 'wild', 'value': 'wild', 'type': 'wild'})
        card_id += 1
        deck.append({'id': card_id, 'color': 'wild', 'value': 'wild_draw4', 'type': 'wild_draw4'})
        card_id += 1
        
    random.shuffle(deck)
    return deck

def calculate_card_points(card):
    val = card['value']
    if val in ['wild', 'wild_draw4']:
        return 50
    elif val in ['skip', 'reverse', 'draw2']:
        return 20
    elif val.isdigit():
        return int(val)
    return 0

def calculate_hand_points(hand):
    return sum(calculate_card_points(c) for c in hand)

class UnoGame:
    def __init__(self, room_code, target_score=250):
        self.room_code = room_code
        self.players = [] # [{sid, name, avatar, hand, is_bot, cards_played_count, called_uno, score}]
        self.deck = []
        self.discard_pile = []
        self.current_player_idx = 0
        self.direction = 1 # 1 for clockwise, -1 for counter-clockwise
        self.current_color = None
        self.status = 'lobby' # 'lobby', 'playing', 'finished'
        self.winner = None
        self.turn_count = 0
        self.target_score = target_score
        self.log_messages = []
        self.round_winner = None
        self.last_round_points = 0
        
    def add_player(self, sid, name, avatar="😃", is_bot=False):
        for p in self.players:
            if p['sid'] == sid:
                p['name'] = name
                p['avatar'] = avatar
                return p
        player = {
            'sid': sid,
            'name': name,
            'avatar': avatar,
            'hand': [],
            'is_bot': is_bot,
            'cards_played_count': 0,
            'called_uno': False,
            'score': 0
        }
        self.players.append(player)
        self.add_log(f"{name} joined the room.")
        return player

    def remove_player(self, sid):
        p_to_rem = None
        for p in self.players:
            if p['sid'] == sid:
                p_to_rem = p
                break
        if p_to_rem:
            self.players.remove(p_to_rem)
            self.add_log(f"{p_to_rem['name']} left the room.")
            if len(self.players) > 0 and self.current_player_idx >= len(self.players):
                self.current_player_idx = 0
            if len(self.players) < 2 and self.status == 'playing':
                self.status = 'lobby'
                self.add_log("Game stopped: Not enough players.")

    def add_bot(self):
        bot_id = f"bot_{random.randint(1000, 9999)}"
        bot_names = ["MegaBot 🤖", "UnoMaster 👑", "CardShark 🦈", "Blaze 🔥", "LuckyStrike 🍀"]
        bot_avatars = ["🤖", "🦊", "🦁", "🐼", "🤖"]
        idx = len([p for p in self.players if p['is_bot']])
        name = bot_names[idx % len(bot_names)]
        avatar = bot_avatars[idx % len(bot_avatars)]
        return self.add_player(bot_id, name, avatar, is_bot=True)

    def setup_quick_bot_game(self, total_players=4):
        # Fill remaining slots with bots up to total_players
        while len(self.players) < total_players:
            self.add_bot()

    def start_game(self):
        if len(self.players) < 2:
            return False, "At least 2 players are needed to start the game."
            
        self.deck = generate_deck()
        self.discard_pile = []
        self.status = 'playing'
        self.current_player_idx = random.randint(0, len(self.players) - 1)
        self.direction = 1
        self.winner = None
        self.round_winner = None
        self.turn_count = 1
        self.log_messages = []
        
        # Deal 7 cards to each player
        for p in self.players:
            p['hand'] = [self.deck.pop() for _ in range(7)]
            p['cards_played_count'] = 0
            p['called_uno'] = False
            
        # Draw initial top card (must not be wild_draw4 for starting)
        top_card = self.deck.pop()
        while top_card['value'] == 'wild_draw4':
            self.deck.append(top_card)
            random.shuffle(self.deck)
            top_card = self.deck.pop()
            
        self.discard_pile.append(top_card)
        
        if top_card['color'] == 'wild':
            self.current_color = random.choice(COLORS)
        else:
            self.current_color = top_card['color']
            
        self.add_log(f"Game started! Starting card is {top_card['color'].upper()} {top_card['value'].upper()}.")
        
        # Handle initial action card effect if any
        if top_card['value'] == 'skip':
            self.add_log(f"Skip card! {self.get_current_player()['name']}'s turn is skipped.")
            self._advance_turn()
        elif top_card['value'] == 'reverse':
            self.direction *= -1
            self.add_log(f"Reverse card! Direction flipped.")
        elif top_card['value'] == 'draw2':
            curr_p = self.get_current_player()
            self.add_log(f"Draw 2 card! {curr_p['name']} draws 2 cards.")
            self._draw_cards_for_player(curr_p, 2)
            self._advance_turn()
            
        return True, "Game started successfully."

    def get_current_player(self):
        if not self.players:
            return None
        return self.players[self.current_player_idx]

    def add_log(self, text):
        self.log_messages.append(text)
        if len(self.log_messages) > 30:
            self.log_messages.pop(0)

    def is_valid_play(self, card):
        top_card = self.discard_pile[-1]
        if card['color'] == 'wild' or card['type'] in ['wild', 'wild_draw4']:
            return True
        if card['color'] == self.current_color:
            return True
        if card['value'] == top_card['value']:
            return True
        return False

    def play_card(self, player_sid, card_id, chosen_color=None):
        if self.status != 'playing':
            return False, "Game is not currently active."
            
        curr_p = self.get_current_player()
        if not curr_p or curr_p['sid'] != player_sid:
            return False, "It's not your turn!"
            
        card_idx = None
        for i, c in enumerate(curr_p['hand']):
            if c['id'] == card_id:
                card_idx = i
                break
                
        if card_idx is None:
            return False, "Card not found in your hand."
            
        card = curr_p['hand'][card_idx]
        
        if not self.is_valid_play(card):
            return False, f"Invalid card play! Card must match color {self.current_color.upper()} or symbol {self.discard_pile[-1]['value'].upper()}."
            
        curr_p['hand'].pop(card_idx)
        curr_p['cards_played_count'] += 1
        self.discard_pile.append(card)
        
        if len(curr_p['hand']) > 1:
            curr_p['called_uno'] = False

        if card['color'] == 'wild' or card['type'] in ['wild', 'wild_draw4']:
            if not chosen_color or chosen_color not in COLORS:
                chosen_color = random.choice(COLORS)
            self.current_color = chosen_color
            self.add_log(f"{curr_p['name']} played a {card['value'].upper()} and chose {chosen_color.upper()}!")
        else:
            self.current_color = card['color']
            self.add_log(f"{curr_p['name']} played {card['color'].upper()} {card['value'].upper()}.")

        # Check win condition for round
        if len(curr_p['hand']) == 0:
            round_pts = sum(calculate_hand_points(p['hand']) for p in self.players if p['sid'] != curr_p['sid'])
            curr_p['score'] += round_pts
            self.last_round_points = round_pts
            self.round_winner = curr_p
            
            if curr_p['score'] >= self.target_score or len([p for p in self.players if not p['is_bot']]) <= 1:
                self.status = 'finished'
                self.winner = curr_p
                self.add_log(f"🏆 {curr_p['name']} WON THE CHAMPIONSHIP WITH {curr_p['score']} PTS! 🏆")
            else:
                self.status = 'finished'
                self.winner = curr_p
                self.add_log(f"🎉 {curr_p['name']} won the round (+{round_pts} PTS)! Total: {curr_p['score']} PTS.")
            return True, "Win"

        next_turn_advance = 1
        if card['value'] == 'skip':
            next_turn_advance = 2
            self.add_log("Skip card played! Next player's turn is skipped.")
        elif card['value'] == 'reverse':
            if len(self.players) == 2:
                next_turn_advance = 2
                self.add_log("Reverse played! Player gets another turn.")
            else:
                self.direction *= -1
                self.add_log("Reverse card played! Direction changed.")
        elif card['value'] == 'draw2':
            next_p = self._peek_next_player(1)
            self.add_log(f"{next_p['name']} draws 2 cards and turn is skipped!")
            self._draw_cards_for_player(next_p, 2)
            next_turn_advance = 2
        elif card['value'] == 'wild_draw4':
            next_p = self._peek_next_player(1)
            self.add_log(f"{next_p['name']} draws 4 cards and turn is skipped!")
            self._draw_cards_for_player(next_p, 4)
            next_turn_advance = 2

        self._advance_turn(step=next_turn_advance)
        return True, "Card played successfully."

    def player_draw_card(self, player_sid):
        if self.status != 'playing':
            return False, "Game is not active.", None
            
        curr_p = self.get_current_player()
        if not curr_p or curr_p['sid'] != player_sid:
            return False, "It's not your turn!", None
            
        drawn_cards = self._draw_cards_for_player(curr_p, 1)
        if not drawn_cards:
            return False, "Deck is completely empty!", None
            
        drawn_card = drawn_cards[0]
        self.add_log(f"{curr_p['name']} drew a card.")
        
        can_play = self.is_valid_play(drawn_card)
        if not can_play:
            self._advance_turn()
            return True, "Drawn card could not be played. Turn passed.", drawn_card
        else:
            return True, "Drawn card can be played!", drawn_card

    def call_uno(self, player_sid):
        player = None
        for p in self.players:
            if p['sid'] == player_sid:
                player = p
                break
        if not player:
            return False, "Player not found."
            
        if len(player['hand']) == 1:
            player['called_uno'] = True
            self.add_log(f"🔥 {player['name']} called UNO! 🔥")
            return True, f"{player['name']} called UNO!"
        else:
            return False, "You can only call UNO when you have exactly 1 card!"

    def catch_uno_failure(self, caller_sid, target_sid):
        target = None
        for p in self.players:
            if p['sid'] == target_sid:
                target = p
                break
        if not target:
            return False, "Target player not found."
            
        if len(target['hand']) == 1 and not target['called_uno']:
            self._draw_cards_for_player(target, 2)
            self.add_log(f"🚨 {target['name']} was caught not saying UNO! Drew 2 penalty cards.")
            return True, f"{target['name']} drew 2 penalty cards!"
        return False, f"{target['name']} cannot be penalized."

    def _draw_cards_for_player(self, player, count):
        drawn = []
        for _ in range(count):
            if len(self.deck) == 0:
                self._recycle_discard_pile()
            if len(self.deck) > 0:
                card = self.deck.pop()
                player['hand'].append(card)
                drawn.append(card)
        return drawn

    def _recycle_discard_pile(self):
        if len(self.discard_pile) > 1:
            top_card = self.discard_pile.pop()
            self.deck = self.discard_pile
            self.discard_pile = [top_card]
            random.shuffle(self.deck)
            self.add_log("Discard pile recycled back into deck.")

    def _peek_next_player(self, step=1):
        idx = (self.current_player_idx + (self.direction * step)) % len(self.players)
        return self.players[idx]

    def _advance_turn(self, step=1):
        if len(self.players) > 0:
            self.current_player_idx = (self.current_player_idx + (self.direction * step)) % len(self.players)
            self.turn_count += 1
            curr_p = self.get_current_player()
            self.add_log(f"It's {curr_p['name']}'s turn.")

    def bot_take_turn(self):
        curr_p = self.get_current_player()
        if not curr_p or not curr_p['is_bot'] or self.status != 'playing':
            return False
            
        if len(curr_p['hand']) == 2:
            curr_p['called_uno'] = True
            self.add_log(f"🔥 {curr_p['name']} (Bot) called UNO! 🔥")
            
        playable = [c for c in curr_p['hand'] if self.is_valid_play(c)]
        if playable:
            card_to_play = playable[0]
            chosen_color = None
            if card_to_play['color'] == 'wild' or card_to_play['type'] in ['wild', 'wild_draw4']:
                color_counts = {c: 0 for c in COLORS}
                for c in curr_p['hand']:
                    if c['color'] in color_counts:
                        color_counts[c['color']] += 1
                chosen_color = max(color_counts, key=color_counts.get)
                
            self.play_card(curr_p['sid'], card_to_play['id'], chosen_color)
            return True
        else:
            success, msg, drawn_card = self.player_draw_card(curr_p['sid'])
            if drawn_card and self.is_valid_play(drawn_card):
                chosen_color = None
                if drawn_card['color'] == 'wild' or drawn_card['type'] in ['wild', 'wild_draw4']:
                    chosen_color = random.choice(COLORS)
                self.play_card(curr_p['sid'], drawn_card['id'], chosen_color)
            return True

    def to_dict(self, for_sid=None):
        players_data = []
        for p in self.players:
            p_info = {
                'sid': p['sid'],
                'name': p['name'],
                'avatar': p['avatar'],
                'is_bot': p['is_bot'],
                'hand_count': len(p['hand']),
                'called_uno': p['called_uno'],
                'score': p['score'],
                'is_current': (self.get_current_player() and self.get_current_player()['sid'] == p['sid'])
            }
            if for_sid and p['sid'] == for_sid:
                p_info['hand'] = p['hand']
            players_data.append(p_info)
            
        top_discard = self.discard_pile[-1] if self.discard_pile else None
        
        return {
            'room_code': self.room_code,
            'status': self.status,
            'current_player_sid': self.get_current_player()['sid'] if self.get_current_player() else None,
            'direction': self.direction,
            'current_color': self.current_color,
            'top_discard': top_discard,
            'deck_count': len(self.deck),
            'target_score': self.target_score,
            'players': players_data,
            'winner': {'name': self.winner['name'], 'avatar': self.winner['avatar'], 'score': self.winner['score']} if self.winner else None,
            'last_round_points': self.last_round_points,
            'log_messages': self.log_messages[-10:]
        }
