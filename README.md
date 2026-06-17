# Wordle Bot for Nerimity

A feature-rich Wordle bot for [Nerimity](https://nerimity.com) with XP progression, leaderboards, special events, and multiplayer modes.

## ✨ Features

- **Daily Wordle**: Classic 6-guess word puzzle that changes every day
- **Special Events**: Themed Wordle modes (Undertale, Deltarune, Genshin Impact, Forsaken, Vocaloid)
- **XP & Leveling**: 100 levels with unique tier names and progression system
- **Leaderboards**: Daily and all-time rankings with streak tracking
- **Hard Mode**: 2x XP, no hints, must reuse confirmed letters
- **Hints System**: Reveal letters after 2 guesses (costs 2 guesses)
- **Duel Mode**: 1v1 turn-based Wordle battles
- **Streak Tracking**: Build and maintain win streaks across different modes
- **Comeback Bonuses**: 2x XP when returning after a week away
- **Auto Reminders**: Configurable daily reminders via cron

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Node.js 16+ (for Nerimity SDK)
- A Nerimity bot token

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/wordle.git
   cd wordle
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   npm install
   ```

3. Configure environment:
   ```bash
   cp .env.example.py .env
   ```
   
   Edit `.env` and add your credentials:
   ```python
   NERIMITY_TOKEN=your_bot_token_here
   OWNER_USER_ID=your_user_id_here
   REMINDER_CHANNEL_ID=your_channel_id_here
   REMINDER_CRON=0 3 * * *
   ```

4. Run the bot:
   ```bash
   python src_py/bot.py
   ```

## 🎮 Commands

### Core Commands
- `/wordle` - Start or view today's puzzle
- `/answer <word>` - Submit a 5-letter guess
- `/hint` - Reveal 1-2 letters (after 2 guesses, costs 2 guesses)
- `/hard` - Enable hard mode (2x XP, no hints, must reuse confirmed letters)
- `/giveup` - Surrender and reveal the word
- `/share` - Post a spoiler-free emoji grid

### Social Commands
- `/challenge @user` - Ping someone to play
- `/versus @user` - Start a 1v1 Wordle duel (turn-based, no XP)
- `/duelguess <word>` - Make your guess in an active duel

### Stats & Leaderboards
- `/leaderboard` - View today's leaderboard
- `/alltimeleaderboard` - View the hall of fame
- `/mystats` - View your personal statistics

### Special Events
- `/undertale` - Play Undertale Anniversary Wordle (Sept 15)
- `/deltarune` - Play Deltarune Anniversary Wordle (Oct 31)
- `/genshin` - Play Genshin Impact event Wordle
- `/forsaken` - Play Forsaken Update Wordle
- `/vocaloid` - Play Vocaloid Night Wordle

### Help
- `/whelp` or `/help` - Display all commands

## 📊 XP & Leveling System

- **Base XP**: 10 for wins, 5 for losses
- **Hard Mode Multiplier**: 2x XP
- **Streak Bonus**: +10% per consecutive win (stacks)
- **Comeback Bonus**: 2x XP when returning after 7+ days
- **Max Level**: 100 with unique tier names

## 🏆 Game Modes

### Daily Mode
Standard 5-letter English words from a curated list.

### Hard Mode
- 2x XP multiplier
- No hints available
- Must reuse all confirmed (green) letters
- Must include all present (yellow) letters

### Special Events
- **Undertale/Deltarune**: Character names and game terms
- **Genshin Impact**: Character names (5-letter aliases like AYAKA, HUTAO)
- **Forsaken**: Roblox Forsaken character codes
- **Vocaloid**: Vocaloid character names

## 🛠️ Development

### Project Structure

```
wordle/
├── src_py/                 # Python source code
│   ├── bot.py              # Main bot entry point
│   ├── game_logic.py       # Core Wordle game mechanics
│   ├── leaderboard_store.py # Leaderboard management
│   ├── stats.py            # XP and statistics
│   ├── word_list.py        # Word pools
│   └── ...
├── data/                   # JSON data files (runtime)
├── requirements.txt        # Python dependencies
└── package.json            # Node.js configuration
```

### Running Tests

```bash
pytest
```

### Development Mode (auto-restart)

```bash
npm run dev
```

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup instructions
- Coding standards and guidelines
- How to submit pull requests
- Reporting issues

## 📝 License

This project is open source. See the repository for license details.

## 🙏 Credits

Created by [@Kasane:TETO](https://nerimity.com) (Joddabod)

---

**Invite the bot to your Nerimity server and start playing Wordle today!**
