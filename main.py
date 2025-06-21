import requests, time, telegram, os
from datetime import datetime
from dateutil import tz

# === CONFIGURATION ===
BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_USERNAME = '@TellemNewsChannel'
CRYPTO_PANIC_API_KEY = os.environ['CRYPTO_PANIC_API_KEY']
POST_INTERVAL_SECONDS = 900  # 15 minutes

# === INIT BOT ===
bot = telegram.Bot(token=BOT_TOKEN)
last_posted_links = set()

def fetch_crypto_news():
    url = f'https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTO_PANIC_API_KEY}&public=true&kind=news'
    response = requests.get(url)
    data = response.json()
    return data.get('results', [])

def extract_sentiment(title):
    bullish_keywords = ["surge", "soars", "rises", "up", "gains", "approved", "growth"]
    bearish_keywords = ["plunge", "falls", "down", "drop", "loss", "rejected", "hack"]
    
    title_lower = title.lower()
    for word in bullish_keywords:
        if word in title_lower:
            return "Bullish"
    for word in bearish_keywords:
        if word in title_lower:
            return "Bearish"
    return "Neutral"

def format_news_item(item):
    title = item.get('title', 'No Title')
    link = item.get('url', '')
    sentiment = extract_sentiment(title)
    
    # Timestamp in readable format
    published_at = item.get('published_at')
    if published_at:
        utc_time = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
        local_time = utc_time.astimezone(tz.gettz('Africa/Lagos'))
        time_str = local_time.strftime('%I:%M %p')
    else:
        time_str = "Just now"
    
    hashtags = ' '.join(f"#{tag.upper()}" for tag in item.get('currencies', [])[:3])
    
    return f"🚨 [{sentiment}] {title}\n🕒 {time_str}\n{hashtags}"

def post_news():
    global last_posted_links
    news_items = fetch_crypto_news()

    for item in reversed(news_items):
        link = item.get('url')
        if link not in last_posted_links and item.get('importance') == 'high':
            message = format_news_item(item)
            try:
                bot.send_message(chat_id=CHANNEL_USERNAME, text=message, disable_web_page_preview=True)
                last_posted_links.add(link)
                print(f"✅ Posted: {link}")
            except Exception as e:
                print(f"❌ Error posting: {e}")
        time.sleep(2)

while True:
    print("🔄 Checking for high-impact news...")
    post_news()
    time.sleep(POST_INTERVAL_SECONDS)
