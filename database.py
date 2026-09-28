import os
import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/uno_game")

client = None
db = None
is_connected = False

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=4000)
    # Check connection
    client.admin.command('ping')
    db = client['uno_game']
    is_connected = True
    print("Successfully connected to MongoDB Atlas!")
except Exception as e:
    print(f"MongoDB connection warning: {e}. Operating in memory mode for stats.")
    is_connected = False

# Memory storage fallback
memory_users = {}
memory_history = []

def get_or_create_user(username, avatar="😃"):
    username = username.strip()
    if not username:
        username = "Guest"
        
    if is_connected and db is not None:
        users = db['users']
        user = users.find_one({"username": username})
        if not user:
            user = {
                "username": username,
                "avatar": avatar,
                "wins": 0,
                "losses": 0,
                "games_played": 0,
                "cards_played": 0,
                "created_at": datetime.datetime.utcnow()
            }
            users.insert_one(user)
        else:
            users.update_one({"username": username}, {"$set": {"avatar": avatar}})
        return user
    else:
        if username not in memory_users:
            memory_users[username] = {
                "username": username,
                "avatar": avatar,
                "wins": 0,
                "losses": 0,
                "games_played": 0,
                "cards_played": 0
            }
        else:
            memory_users[username]["avatar"] = avatar
        return memory_users[username]

def update_user_stats(username, won=False, cards_played=0):
    if not username or username.startswith("Bot_"):
        return
        
    if is_connected and db is not None:
        users = db['users']
        inc_data = {
            "games_played": 1,
            "cards_played": cards_played
        }
        if won:
            inc_data["wins"] = 1
        else:
            inc_data["losses"] = 1
            
        users.update_one({"username": username}, {"$inc": inc_data})
    else:
        if username in memory_users:
            memory_users[username]["games_played"] += 1
            memory_users[username]["cards_played"] += cards_played
            if won:
                memory_users[username]["wins"] += 1
            else:
                memory_users[username]["losses"] += 1

def get_leaderboard(limit=10):
    if is_connected and db is not None:
        try:
            users = db['users'].find().sort("wins", -1).limit(limit)
            result = []
            for u in users:
                result.append({
                    "username": u["username"],
                    "avatar": u.get("avatar", "😃"),
                    "wins": u.get("wins", 0),
                    "losses": u.get("losses", 0),
                    "games_played": u.get("games_played", 0),
                    "cards_played": u.get("cards_played", 0)
                })
            return result
        except Exception as e:
            print("Error fetching leaderboard:", e)
            
    # Fallback to memory
    sorted_users = sorted(memory_users.values(), key=lambda x: x.get("wins", 0), reverse=True)
    return sorted_users[:limit]

def save_game_history(room_code, winner_name, total_turns, players):
    record = {
        "room_code": room_code,
        "winner": winner_name,
        "total_turns": total_turns,
        "players": players,
        "played_at": datetime.datetime.utcnow()
    }
    if is_connected and db is not None:
        try:
            db['game_history'].insert_one(record)
        except Exception as e:
            print("Error saving game history:", e)
    else:
        memory_history.append(record)
