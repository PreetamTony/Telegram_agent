# Telegram Bot with AI and MongoDB Integration

## Overview
This is a Telegram bot that integrates AI capabilities using Google's Gemini AI, MongoDB for database storage, and Google Custom Search for web searches. The bot can handle text messages, images, and PDF files while providing intelligent responses and analyses.

## Features
- **User Registration:** Stores user details in MongoDB.
- **AI Chatbot:** Generates responses using Gemini AI.
- **Image Analysis:** Describes uploaded images using AI.
- **PDF Processing:** Extracts text and analyzes images from PDFs.
- **Web Search:** Retrieves and summarizes Google search results.

## Setup Instructions

### Prerequisites
Ensure you have the following installed:
- Python 3.8+
- `pip` for package management
- MongoDB Atlas (or a local MongoDB instance)
- A Google API Key for Custom Search
- A Gemini AI API Key
- A Telegram Bot Token

### Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/your-repo/telegram-bot.git
   cd telegram-bot
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Set up environment variables by creating a `.env` file:
   ```env
   TELEGRAM_BOT_TOKEN=your-telegram-bot-token
   MONGODB_USERNAME=your-mongodb-username
   MONGODB_PASSWORD=your-mongodb-password
   MONGODB_CLUSTER=your-mongodb-cluster
   GEMINI_API_KEY=your-gemini-api-key
   GOOGLE_SEARCH_API_KEY=your-google-api-key
   GOOGLE_SEARCH_ENGINE_ID=your-search-engine-id
   ```

## Usage

### Running the Bot
Start the bot with:
```sh
python bot.py
```

### Commands
- `/start` - Registers the user and begins interaction.
- `/websearch` - Prompts the user for a query and performs a Google search.

### Handling Messages
- Text messages receive AI-generated responses.
- Images are analyzed and described.
- PDFs are processed to extract text and analyze images.

## Technologies Used
- **Python** (Primary Language)
- **MongoDB** (Database)
- **Telebot** (Telegram Bot API)
- **Google Generative AI (Gemini)**
- **Google Custom Search API**
- **Pillow** (Image Processing)
- **PyMuPDF** (PDF Processing)

## Deployment
To deploy the bot on a server:
1. Use a cloud VM (e.g., AWS, GCP, or DigitalOcean).
2. Set up a process manager like `screen`, `tmux`, or `systemd`.
3. Run `python bot.py` in the background.

## Troubleshooting
- Ensure all API keys are correct.
- Check MongoDB connection credentials.
- Use `logging` to debug errors.

## License
This project is licensed under the MIT License.

