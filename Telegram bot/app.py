import os
from dotenv import load_dotenv
import telebot
from pymongo import MongoClient
import google.generativeai as genai
import requests
from googleapiclient.discovery import build
from urllib.parse import quote_plus
import logging
from PIL import Image
from io import BytesIO
import base64

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# Set up Telegram bot
bot = telebot.TeleBot(os.getenv('TELEGRAM_BOT_TOKEN'))

# Set up MongoDB with properly encoded username and password
mongodb_username = quote_plus(os.getenv('MONGODB_USERNAME'))
mongodb_password = quote_plus(os.getenv('MONGODB_PASSWORD'))
mongodb_cluster = os.getenv('MONGODB_CLUSTER')
mongodb_uri = f"mongodb+srv://{mongodb_username}:{mongodb_password}@{mongodb_cluster}/?retryWrites=true&w=majority"

try:
    client = MongoClient(mongodb_uri)
    client.admin.command('ismaster')  # Verify MongoDB connection
    logging.info("MongoDB connection successful")
    db = client['telegram_bot']
    users_collection = db['users']
    chats_collection = db['chats']
except Exception as e:
    logging.error(f"MongoDB connection failed: {e}")
    raise

# Set up Gemini AI
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')

# Set up Google Custom Search
search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
google_api_key = os.getenv('GOOGLE_SEARCH_API_KEY')

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    try:
        user = users_collection.find_one({'chat_id': chat_id})
        if not user:
            users_collection.insert_one({
                'chat_id': chat_id,
                'first_name': message.from_user.first_name,
                'username': message.from_user.username
            })
            bot.send_message(chat_id, "Welcome! Please share your contact to complete registration.", 
                             reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
                             .add(telebot.types.KeyboardButton('Share Contact', request_contact=True)))
        else:
            bot.send_message(chat_id, "Welcome back! How can I assist you today?")
    except Exception as e:
        logging.error(f"Error in start function: {e}")
        bot.send_message(chat_id, "An error occurred. Please try again later.")

@bot.message_handler(content_types=['contact'])
def contact(message):
    chat_id = message.chat.id
    phone_number = message.contact.phone_number

    users_collection.update_one({'chat_id': chat_id}, {'$set': {'phone_number': phone_number}})
    bot.send_message(chat_id, "Registration complete! How can I assist you?", 
                     reply_markup=telebot.types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'document'])
def handle_message(message):
    chat_id = message.chat.id

    if message.content_type == 'text' and not message.text.startswith('/'):
        response = generate_response(message.text)
        bot.reply_to(message, response)

        chats_collection.insert_one({
            'user_id': chat_id,
            'user_message': message.text,
            'bot_response': response
        })

    elif message.content_type in ['photo', 'document']:
        file_info = bot.get_file(message.photo[-1].file_id if message.content_type == 'photo' else message.document.file_id)
        file_url = f"https://api.telegram.org/file/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/{file_info.file_path}"
        
        analysis = analyze_file(file_url)
        bot.reply_to(message, analysis)

        chats_collection.insert_one({
            'user_id': chat_id,
            'file_metadata': {
                'filename': message.document.file_name if message.content_type == 'document' else 'image.jpg',
                'description': analysis
            }
        })

@bot.message_handler(commands=['websearch'])
def web_search(message):
    chat_id = message.chat.id
    bot.reply_to(message, "Please enter your search query:")
    bot.register_next_step_handler(message, perform_web_search)

def perform_web_search(message):
    query = message.text
    search_results = google_search(query)
    bot.reply_to(message, search_results, parse_mode='Markdown')

def generate_response(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logging.error(f"Error generating response: {e}")
        return "I'm having trouble processing your request right now. Please try again later."

def analyze_file(file_url):
    """
    Analyze either an image or a PDF based on the file type.
    """
    try:
        response = requests.get(file_url)
        content_type = response.headers.get('Content-Type')

        # Check for PDF or image file types (including .jpeg, .jpg, .png, etc.)
        if content_type == 'application/pdf' or file_url.lower().endswith('.pdf'):
            analysis = analyze_pdf(response.content)
        elif content_type.startswith('image/') or file_url.lower().endswith(('.jpeg', '.jpg', '.png', '.gif', '.bmp')):
            analysis = analyze_image(response.content)
        else:
            analysis = "Unsupported file type. Please upload an image or PDF file."

        return analysis
    except Exception as e:
        logging.error(f"Error analyzing file: {e}")
        return "There was an error processing the file. Please try again later."


def analyze_image(image_bytes):
    """
    Analyze an image and return its description.
    """
    try:
        img = Image.open(BytesIO(image_bytes))
        
        # Convert the image to RGB mode if it's not already
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize the image if it's too large
        max_size = 1024
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size))
        
        # Convert the image to base64
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        analysis = model.generate_content([ 
            "Analyze this image and describe its contents:",
            {"mime_type": "image/jpeg", "data": img_str}
        ])
        return analysis.text
    except Exception as e:
        logging.error(f"Error analyzing image: {e}")
        return "I couldn't process the image. Please try again later."

def analyze_pdf(pdf_content):
    """
    Analyze a PDF by extracting text and images.
    """
    try:
        import fitz  # PyMuPDF
        
        # Open the PDF from the byte stream
        pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
        logging.info("PDF opened successfully.")
        
        results = []

        # Extract text and images from each page
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            
            # Extract text
            text = page.get_text()
            if text.strip():
                results.append(f"Page {page_num + 1} Text:\n{text}\n")

            # Extract images
            images = page.get_images(full=True)
            for img_index, img in enumerate(images):
                xref = img[0]
                base_image = pdf_document.extract_image(xref)
                image_bytes = base_image["image"]

                # Analyze the extracted image
                img_analysis = analyze_image(image_bytes)
                results.append(f"Page {page_num + 1}, Image {img_index + 1} Analysis:\n{img_analysis}\n")

        pdf_document.close()
        return "\n".join(results) if results else "No text or images found in the PDF."
    except Exception as e:
        logging.error(f"Error analyzing PDF: {e}")
        return "There was an error processing the PDF. Please ensure it is a valid PDF file."

def google_search(query):
    try:
        service = build("customsearch", "v1", developerKey=google_api_key)
        result = service.cse().list(q=query, cx=search_engine_id, num=5).execute()

        summaries = []
        for item in result['items']:
            summary = generate_response(f"Summarize this in one sentence: {item['snippet']}")
            summaries.append(f"- [{item['title']}]({item['link']}): {summary}")

        return f"Here's a summary of the top search results for '{query}':\n\n" + "\n\n".join(summaries)
    except Exception as e:
        logging.error(f"Error performing web search: {e}")
        return "I couldn't perform the search. Please try again later."

if __name__ == '__main__':
    logging.info("Bot is running...")
    bot.polling()
