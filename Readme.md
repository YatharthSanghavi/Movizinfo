# 🎬 Moviezinfo Bot

A powerful Telegram bot that provides detailed information about movies and TV series, complete with recommendations, trailers, and IMDb integration.

## ✨ Features

### 🔍 Search Capabilities
- **Movie Search**: Get comprehensive information about any movie
- **Series Search**: Detailed TV series information with episode data
- **Season Search**: Specific season information with episode listings
- **Smart Detection**: Automatically detects whether you're searching for a movie or series

### 📊 Rich Information Display
- Movie/Series posters and details
- IMDb ratings and links
- Cast, director, and writer information
- Genre, release date, and runtime
- Awards and country information
- Language and content rating

### 🎯 Intelligent Recommendations
- Genre-based recommendations for movies and series
- Personalized suggestions based on your searches
- Cached recommendations for faster responses

### 🔗 External Links
- Direct trailer links via YouTube search
- Watch links for movies and series
- Shortened URLs using MDisk API
- IMDb integration for detailed information

### 🛡️ Moderation Features
- Message filtering with custom keywords
- Automatic message deletion for filtered content
- Group and channel management

### 👨‍💻 Developer Tools
- Broadcasting system for announcements
- Statistics tracking
- Cache management
- User interaction monitoring
- API usage tracking with daily limits

## 🚀 Getting Started

### Prerequisites
- Python 3.7+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- OMDB API Key (from [OMDb API](http://www.omdbapi.com/apikey.aspx))
- MDisk API Key (for URL shortening)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YatharthSanghavi/Movizinfo.git
   cd Movizinfo
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Setup**
   
   Create a `.env` file in the root directory:
   ```env
   BOT_TOKEN=your_telegram_bot_token
   OMDB_API_KEY=your_omdb_api_key
   MDISK_API_KEY=your_mdisk_api_key
   DEVELOPER_ID=your_telegram_user_id
   GROUP_IDS=[]
   CHANNEL_IDS=[]
   ENVIRONMENT=development
   ```

4. **Run the bot**
   ```bash
   python movie_filter_bot.py
   ```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BOT_TOKEN` | Telegram bot token from BotFather | ✅ |
| `OMDB_API_KEY` | API key for movie/series data | ✅ |
| `MDISK_API_KEY` | API key for URL shortening | ✅ |
| `DEVELOPER_ID` | Your Telegram user ID for admin commands | ✅ |
| `GROUP_IDS` | JSON array of group IDs (auto-managed) | ❌ |
| `CHANNEL_IDS` | JSON array of channel IDs (auto-managed) | ❌ |
| `ENVIRONMENT` | Set to 'production' for webhook mode | ❌ |
| `WEBHOOK_URL` | Base URL for webhook (production only) | ❌ |
| `PORT` | Port for Flask app (default: 5000) | ❌ |

### Filtered Words Configuration

The bot supports message filtering through `filtered_words.json`:
```json
["inappropriate_word1", "spam_word2"]
```

## 📱 Bot Commands

### User Commands
- `/start` - Welcome message and bot introduction
- `/help` - List of available commands and usage
- `/recommend` - Get movie/series recommendations by genre
- `/id` - Get your Telegram user ID
- `/info` - Display your profile information

### Search Methods
- **Direct Search**: Simply type the movie or series name
- **Season Search**: Type "series name season number" (e.g., "Breaking Bad season 1")

### Developer Commands (Admin Only)
- `/devinfo` - Bot and system information
- `/stats` - Usage statistics
- `/clearcache` - Clear the bot's cache
- `/broadcast` - Send message to all users and groups
- `/broadcast_status` - View tracked channels and groups
- `/filter <word>` - Add word to filter list
- `/reload` - Reload bot configuration

## 🏗️ Architecture

### Core Components

1. **Search Engine**: Handles movie/series queries using OMDB API
2. **Recommendation System**: Provides intelligent suggestions based on genres
3. **Caching Layer**: Reduces API calls and improves response times
4. **Message Filter**: Moderates content in groups and channels
5. **Broadcasting System**: Manages announcements to users and groups

### API Integration

- **OMDB API**: Primary source for movie and TV series data
- **MDisk API**: URL shortening for cleaner links
- **Telegram Bot API**: Core bot functionality
- **YouTube Search**: Trailer and watch links

### Data Flow

```
User Query → Search Detection → API Call → Data Processing → Response Formatting → User Response
```

## 🚀 Deployment

### Local Development
```bash
python movie_filter_bot.py
```

### Production Deployment (Render/Heroku)

1. **Set environment variables** in your hosting platform
2. **Configure webhook** by setting:
   - `ENVIRONMENT=production`
   - `WEBHOOK_URL=https://your-app-url.com/`
3. **Deploy** using your platform's deployment method

### Vercel Deployment

The project includes `vercel.json` for easy Vercel deployment:
```bash
vercel --prod
```

## 📊 Features in Detail

### Smart Search Detection
The bot automatically detects search intent:
- Movie names → Movie search
- Series names → Series search  
- "Series Season X" → Season-specific search

### Recommendation Engine
- Genre-based filtering
- Randomized suggestions
- 24-hour caching for performance
- Support for both movies and series

### Message Filtering
- Custom keyword filtering
- Automatic message deletion
- Temporary notification messages
- Group moderation support

### Broadcasting System
- Mass messaging to all users
- Channel and group announcements
- Status tracking and reporting

## 🔒 Security Features

- Developer-only admin commands
- User ID verification for sensitive operations
- Rate limiting for API calls
- Secure environment variable handling

## 📈 Performance Optimization

- **Caching System**: Reduces API calls by 80%
- **Daily API Limits**: Prevents quota exhaustion
- **Message Cleanup**: Automatic deletion to reduce clutter
- **Efficient Data Processing**: Optimized response formatting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/YatharthSanghavi/Movizinfo/issues)

## 🙏 Acknowledgments

- [OMDB API](http://www.omdbapi.com/) for movie and TV series data
- [MDisk](https://mdiskshortner.link/) for URL shortening services

## 📋 Changelog

### v1.0.0 (Current)
- Initial release with full movie/series search
- Recommendation system implementation
- Message filtering and moderation
- Broadcasting capabilities
- Admin panel and statistics

---

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=YatharthSanghavi/Movizinfo&type=Date)](https://star-history.com/#YatharthSanghavi/Movizinfo&Date)

---

<div align="center">
  <strong>Made with ❤️ by Yatharth</strong>
  <br>
  <br>
  <a href="https://github.com/YatharthSanghavi/Movizinfo/">⭐ Star this repo if you found it helpful!</a>
</div>
