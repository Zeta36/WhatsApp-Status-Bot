# WhatsApp Status Bot

A Python-based automation tool that generates a rich multimedia video (images, narration, and subtitles) from a topic and publishes it as a WhatsApp Status using Selenium.

---

## 🚀 Features

- **Web Research**: Fetches information or ideas for deep quotes using OpenAI.
- **Script Generation**: Generates a custom aphorism or quote of a specified word length.
- **Image Illustration**: Creates high-quality images per segment of the quote using OpenAI image API.
- **Text-to-Speech**: Produces narration audio in configurable voices and tones.
- **Video Assembly**: Combines images, subtitles (PIL-based), and audio into a single MP4 via MoviePy.
- **WhatsApp Publishing**: Automates WhatsApp Web to post the generated video as a Status.
- **Configurable via `.env`**: All parameters (models, counts, styles, captions) are environment-driven.
- **Session Handling**: Headless Chrome session reuse; falls back to visible QR scan when needed.

---

## 📂 Project Structure

```
whatsapp_status_bot/
├── .env                         # Environment variables configuration
├── main.py                      # Orchestrator: search → script → images → audio → video → publish
├── README.md                    # This documentation file
├── requirements.txt (optional)  # List of Python dependencies
├── utils/
│   ├── helper.py               # Bootstrap and run directory utilities
│   └── selenium_helper.py      # Selenium session and publish logic
├── my_agents/
│   ├── websearch_agent.py      # Web search agent using OpenAI and custom instructions
│   ├── script_agent.py         # Quote/aphorism generation with dynamic word count
│   ├── illustration_agent.py   # Image generation agent splitting text into prompts
│   └── tts_agent.py            # Text-to-speech agent
├── tests/
│   └── test_publish.py         # Standalone test script for WhatsApp publishing
└── selenium_profile/           # Persistent Chrome profile for WhatsApp sessions
```

---

## 🛠️ Prerequisites

- Python 3.8+
- Chrome browser & [ChromeDriver](https://chromedriver.chromium.org/) matching your Chrome version
- A valid OpenAI API key with `OPENAI_API_KEY` set

---

## ⚙️ Configuration (`.env`)

Create a `.env` file at the project root with these variables:

```ini
OPENAI_API_KEY=your_openai_api_key

# Web Research & Script
WEB_SEARCH_TOPIC="Your topic here"
SCRIPT_TOPIC="Quote style or theme"
VIDEO_TEXT_LEN="Number of words for the generated quote"
CAPTION_TEXT="Caption to overlay on video"

# Models & Generation Settings
WEB_SEARCH_MODEL="gpt-4o"
SCRIPT_MODEL="o4-mini"
IMAGE_GEN_MODEL="gpt-image-1"
IMAGE_STYLE="Describe desired style"
IMAGE_QUALITY="low|medium|high"
IMAGE_COUNT="Number of images to generate"
SUBTITLE_FONT_SIZE="Font size for subtitles"

# Text-to-Speech
TTS_MODEL="gpt-4o-mini-tts"
TTS_VOICE="Voice identifier"
TTS_TONE="Describe vocal tone and style"

# Selenium
CHROMEDRIVER_PATH="/path/to/chromedriver"
WHATSAPP_PROFILE_DIR="./selenium_profile"
```

---

## 🎬 Usage

1. Install dependencies (example):
   ```bash
   pip install moviepy pillow numpy selenium openai python-dotenv
   ```
2. Configure your `.env` as above.
3. Generate and publish:
   ```bash
   python main.py
   ```

---

## 🧪 Testing

- Run `tests/test_publish.py` to verify WhatsApp Web publishing logic independently.

---

## 🤝 Contributing

Feel free to open issues or pull requests for enhancements or bug fixes.

---

## 📜 License

Distributed under the MIT License.
