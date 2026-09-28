# 🎴 UNO! Online Multiplayer Game

A real-time, feature-rich **Multiplayer UNO Game** powered by **Python (Flask-SocketIO)**, **MongoDB Atlas**, HTML5, CSS3, and Web Audio API. Play with friends online across devices, send live chat messages and floating animated emoji reactions, test skills against smart AI bots, and track player stats on global leaderboards!

---

## 🔥 Key Features

- **🌐 Real-Time Online Multiplayer**: Create or join rooms with a 6-character room code. Play with up to 6 players per room.
- **🤖 Smart AI Bots**: Add bot opponents when playing solo or filling lobby slots.
- **🎴 Complete Official UNO Rules**:
  - Number cards (0-9) in 4 colors (Red, Blue, Green, Yellow).
  - Special action cards: **Skip (🚫)**, **Reverse (🔄)**, **Draw 2 (+2)**.
  - Wild cards: **Wild Color Picker (🎨)**, **Wild Draw 4 (+4)**.
  - **"SHOUT UNO!"** button with non-call catch penalty mechanism (+2 cards).
- **💥 Animated Floating Emojis**: Send real-time floating particle emoji reactions (🔥, 😂, 😭, 😡, 👑, 😱, 🎉) that float across all players' screens!
- **💬 Live Room Chat Drawer**: Integrated real-time chat with avatars and timestamps.
- **🔊 Web Audio API Sound Effects**: Built-in sound synthesizer for card slaps, draws, UNO shouts, turn chimes, and victory fanfares.
- **🍃 MongoDB Atlas Database Integration**:
  - Automatically stores user profiles, wins, losses, cards played, and match history.
  - Real-time Leaderboard displaying top players.
- **🎨 Modern Dark Neon UI**: Glassmorphic cards, 3D card tilt/hover animations, circular turn indicator ring, and dynamic color banners.

---

## 🛠️ Installation & Setup Guide

### Prerequisites
- Python 3.10+ installed on your computer.

### 1-Click Launch (Windows)
Simply double-click `run_game.bat`!

### Manual Launch
1. Clone the repository:
   ```bash
   git clone https://github.com/Mouleeshwaranv/UNO.git
   cd UNO
   ```

2. Install dependencies:
   ```bash
   py -m pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   py app.py
   ```

4. Open your browser at:
   `http://localhost:5000` (or share your local IP with friends on the same network!).

---

## 📁 Project Structure

```
UNO/
├── app.py              # Flask server & SocketIO event handlers
├── uno_logic.py        # UNO card rules, deck generator, game engine & bot AI
├── database.py         # MongoDB Atlas connection & stats persistence
├── requirements.txt    # Python package dependencies
├── .env                # MongoDB URI & server secret configuration
├── .gitignore          # Git ignore rules
├── run_game.bat        # Windows 1-click startup script
├── static/
│   ├── css/
│   │   └── style.css   # Dark neon theme, animations & responsive layout
│   └── js/
│       ├── audio.js    # Web Audio API sound synthesizer
│       └── game.js     # SocketIO client events & card rendering
└── templates/
    └── index.html      # Responsive HTML5 UI templates & modals
```

---

## 🏆 GitHub Repository

Uploaded to GitHub: [https://github.com/Mouleeshwaranv/UNO](https://github.com/Mouleeshwaranv/UNO)
