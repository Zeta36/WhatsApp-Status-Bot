# WhatsApp Status Bot

A Python-based automation tool that generates rich multimedia videos (images, narration, subtitles, and background music) from a topic and publishes them as WhatsApp Status updates using Selenium.

---

## 🚀 Features

- **Web Research**: Fetches information or ideas using OpenAI.
- **Script Generation**: Creates custom content with configurable length and style.
- **Language Detection & Translation**: Automatically detects non-Spanish content and translates it.
- **Script Transformation**: Applies custom transformations to scripts using AI.
- **Image Generation**: Creates high-quality images using OpenAI's DALL-E or fetches relevant images via Bing.
- **Text-to-Speech**: Produces natural-sounding narration with configurable voices and tones.
- **Video Assembly**: Combines images, subtitles, audio, and background music into a single MP4.
- **Custom Audio Support**: Option to use pre-recorded audio files instead of generating TTS.
- **WhatsApp Publishing**: Automates WhatsApp Web to post the generated video as a Status.
- **Advanced Configuration**: Extensive `.env` configuration for all parameters.
- **Session Handling**: Persistent Chrome profile for WhatsApp Web sessions.

---

## 📂 Project Structure

```
whatsapp_status_bot/
├── .env                         # Environment variables configuration
├── main.py                      # Main orchestrator script
├── README.md                    # This documentation file
├── requirements.txt             # Python dependencies
├── get_chromedriver.sh          # Script to download ChromeDriver
├── utils/
│   ├── helper.py               # Bootstrap and run directory utilities
│   ├── selenium_helper.py      # Selenium session and publish logic
│   └── video_helper.py         # Video generation and processing utilities
├── my_agents/                  # AI-powered agents
│   ├── websearch_agent.py      # Web search using OpenAI and custom instructions
│   ├── script_agent.py         # Content generation with dynamic word count
│   ├── script_transform_agent.py # Applies custom transformations to scripts
│   ├── illustration_agent.py   # Image generation using DALL-E
│   ├── web_image_agent.py      # Fetches images from the web via Bing
│   ├── tts_agent.py            # Text-to-speech generation
│   ├── title_agent.py          # Generates engaging titles
│   └── langcheck_agent.py      # Language detection and translation
├── tests/                      # Test scripts
│   └── test_publish.py         # WhatsApp publishing tests
├── media/                      # Media assets (custom audio, etc.)
└── selenium_profile/           # Persistent Chrome profile for WhatsApp
```

---

## 🛠️ Prerequisites

- Python 3.10+
- Chrome browser & [ChromeDriver](https://chromedriver.chromium.org/) (use `get_chromedriver.sh` for easy setup)
- A valid OpenAI API key with access to GPT-4 and DALL-E models
- FFmpeg (for video processing)
- SoX (for audio processing, optional but recommended)

---

## ⚙️ Configuration (`.env`)

Create a `.env` file at the project root with these variables:

```ini
# API Keys
OPENAI_API_KEY=your_openai_api_key
BING_API_KEY=your_bing_search_key  # Required for web image search

# Content Generation
WEB_SEARCH_TOPIC="Your topic here"
SCRIPT_TOPIC="Content style or theme"
VIDEO_TEXT_LEN=150  # Target word count
CAPTION_TEXT="Caption to overlay on video"

# Model Selection
WEB_SEARCH_MODEL="gpt-4"
SCRIPT_MODEL="gpt-4"
SCRIPT_TRANSFORM_MODEL="gpt-4"
TITLE_MODEL="gpt-4"
IMAGE_GEN_MODEL="dall-e-3"
TTS_MODEL="tts-1"

# Image Generation
IMAGE_STYLE="photorealistic"
IMAGE_QUALITY="hd"  # standard or hd
IMAGE_COUNT=3
KEYWORK_IMAGE_SEARCH="true"  # Use web search for image keywords

# Text-to-Speech
TTS_VOICE="alloy"  # alloy, echo, fable, onyx, nova, or shimmer
TTS_TONE="professional"

# Audio Processing
VOICE_VOLUME=1.0
MUSIC_VOLUME=0.5
SILENCE_DURATION=3.0  # seconds of silence at start/end
USE_CUSTOM_AUDIO=false
CUSTOM_AUDIO_FILE="input.mp3"

# Video Settings
SUBTITLE_FONT_SIZE=48
SUBTITLE_COLOR="white"
BACKGROUND_COLOR="#000000"

# Selenium Configuration
CHROMEDRIVER_PATH="/usr/local/bin/chromedriver"
WHATSAPP_PROFILE_DIR="./selenium_profile"

# Script Options
USE_SCRIPT_FILE=false  # Use script.txt from media folder
USE_CAPTION_FILE=false  # Use caption.txt from media folder
```

---

## 🎬 Installation & Usage

1. Clone the repository and navigate to the project directory.

2. Install dependencies:
   ```bash
   # Create and activate a virtual environment (recommended)
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Install ChromeDriver (Linux/macOS)
   chmod +x get_chromedriver.sh
   ./get_chromedriver.sh
   ```

3. Configure your `.env` file with your API keys and preferences.

4. Run the bot:
   ```bash
   python main.py
   ```

5. For custom audio mode, place your audio file in the `media` folder and set `USE_CUSTOM_AUDIO=true` in `.env`.

### Advanced Usage

- Use `USE_SCRIPT_FILE=true` to read script from `media/script.txt`
- Use `USE_CAPTION_FILE=true` to read caption from `media/caption.txt`
- Set `KEYWORK_IMAGE_SEARCH=true` to enhance image generation with web search
- Adjust audio levels with `VOICE_VOLUME` and `MUSIC_VOLUME`

---

## 🧪 Testing

- Run the test suite:
  ```bash
  python -m pytest tests/
  ```

- Test WhatsApp Web publishing independently:
  ```bash
  python tests/test_publish.py
  ```

## 🔄 Automation

To run the bot on a schedule, use cron (Linux/macOS) or Task Scheduler (Windows). Example cron job to run daily at 9 AM:

```bash
# Edit crontab
crontab -e

# Add this line (adjust paths as needed)
0 9 * * * cd /path/to/whatsapp_status_bot && /path/to/venv/bin/python main.py >> cron.log 2>&1
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

## 📞 Support

For support, please open an issue in the GitHub repository.
