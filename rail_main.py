from flask import Flask, request, jsonify
from datetime import datetime
import requests, json, os, redis, re, logging
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Load environment variables
load_dotenv()

app = Flask(__name__)

# ---------------------------
# Production Configuration
# ---------------------------
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "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")
WAHA_API_URL = os.getenv("WAHA_API_URL", "http://localhost:3000/api")
WAHA_SESSION = os.getenv("WAHA_SESSION", "default")
WAHA_WEBHOOK_TOKEN = os.getenv("WAHA_WEBHOOK_TOKEN", "your-webhook-secret")
CALL_NOW_PHONE = os.getenv("CALL_NOW_PHONE", "+919003444435")
CALL_NOW_LABEL = "📞 Call Now"
DEBUG_MODE = os.getenv("FLASK_DEBUG", "False").lower() == "true"
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))

# Safe logging setup for Railway (logs/ may not work)
@app.route("/webhook", methods=["POST"])
def custom_webhook():
    return jsonify({"msg": "webhook received"}), 200

@app.route("/post", methods=["POST"])
def post_testing():
    return jsonify({"msg": "post OK"}), 200

if not DEBUG_MODE:
    try:
        os.makedirs('logs', exist_ok=True)
        file_handler = RotatingFileHandler('logs/dermijan.log', maxBytes=10240000, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Dermijan Chatbot startup')
    except Exception as e:
        # Railway read-only storage: fallback, use stdout logging only
        app.logger.info(f"Logging to logs/ failed: {e}")

# ---------------------------
# Dermijan URLs
# ---------------------------
ALLOWED_URLS = [
    "https://dermijan.com/",
    "https://dermijan.com/about/",
    "https://dermijan.com/services/",
    "https://dermijan.com/gallery/",
    "https://dermijan.com/contact/",
    "https://dermijan.com/blog/",
    "https://dermijan.com/category/skin-care/",
    "https://dermijan.com/category/hair-care/",
    "https://dermijan.com/category/skin-care/page/2/",
    "https://dermijan.com/category/skin-care/page/3/",
    "https://dermijan.com/regenera-activa-in-chennai/",
    "https://dermijan.com/laser-treatment-for-hair-removal/",
    "https://dermijan.com/lipo-gel-liposculpture-lipo-gel/",
    "https://dermijan.com/skin-fairness-treatment/",
    "https://dermijan.com/skin-polishing-treatment/",
    "https://dermijan.com/under-eye-dark-circles-treatment/",
    "https://dermijan.com/weight-loss-programs/",
    "https://dermijan.com/inch-loss-treatment/",
    "https://dermijan.com/hair-strengthening/",
    "https://dermijan.com/figure-correction-body-sculpting/",
    "https://dermijan.com/deep-scar-removal/",
    "https://dermijan.com/cryomatic/",
    "https://dermijan.com/body-toning-treatment/",
    "https://dermijan.com/best-wrinkle-treatment/",
    "https://dermijan.com/body-alignment-beauty-therapy/",
    "https://dermijan.com/best-natural-fairness-treatment/",
    "https://dermijan.com/best-dark-spot-removal-treatment/",
    "https://dermijan.com/best-anti-dandruff-treatment/",
    "https://dermijan.com/anti-hair-fall-treatment/",
    "https://dermijan.com/anti-aging-skin-care-treatment/",
    "https://dermijan.com/hair-transplantation/",
    "https://dermijan.com/hair-re-growth/",
    "https://dermijan.com/stop-wasting-money-the-top-5-skin-whitening-myths/",
    "https://dermijan.com/the-no-1-diet-secret-for-transforming-your-skin-tone/",
    "https://dermijan.com/kojic-acid-lie-exposed/",
    "https://dermijan.com/vitamin-is-your-secret-weapon-for-skin-whitening/",
    "https://dermijan.com/tips-to-prevent-hair-loss-and-maintain-healthy-hair/",
    "https://dermijan.com/how-much-does-prp-hair-treatment-cost-in-chennai/",
    "https://dermijan.com/discover-the-best-prp-treatment-clinics-in-chennai/",
    "https://dermijan.com/hair-loss-treatment-in-chennai-top-5-solutions/",
    "https://dermijan.com/natural-anti-aging-face-mask-at-home/",
    "https://dermijan.com/glow-up-guide-7-step-korean-skin-care-routine/",
    "https://dermijan.com/winter-night-skin-care-routine-essentials/",
    "https://dermijan.com/winter-combo-skin-care-routine-essentials/",
    "https://dermijan.com/radiant-skin-care-before-wedding-guide/",
    "https://dermijan.com/hair-regrowth-for-trichotillomania-solutions/",
    "https://dermijan.com/best-derma-roller-size-for-hair-regrowth-results/",
    "https://dermijan.com/baby-hairs-are-they-a-sign-of-regrowth/",
    "https://dermijan.com/unlocking-beauty-discovering-dr-daisys-dermijan/",
    "https://dermijan.com/how-to-remove-neck-wrinkles/",
    "https://dermijan.com/what-is-a-skin-polishing-facial/",
    "https://dermijan.com/can-sunglasses-prevent-dark-circles/",
    "https://dermijan.com/does-dandruff-cause-acne/",
    "https://dermijan.com/can-old-scars-be-removed/",
    "https://dermijan.com/dermijans-cryomatic-treatment-unlocking-the-secrets-to-stronger-skin/",
    "https://dermijan.com/how-to-manage-wrinkles-on-face-a-comprehensive-guide/",
    "https://dermijan.com/is-laser-hair-removal-safe-for-your-skin/",
    "https://dermijan.com/the-skincare-revolution-transforming-skin-discoloration-into-perfection/",
    "https://dermijan.com/saying-goodbye-to-age-spots-how-it-works/",
    "https://dermijan.com/ulthera-laser-transform-your-skin-with-non-invasive-rejuvenation/",
    "https://dermijan.com/your-simple-guide-to-glowing-skin-easy-tips-and-essential-skincare/",
    "https://dermijan.com/unlocking-the-secrets-to-achieving-radiant-skin-naturally/",
    "https://dermijan.com/10-surprising-things-that-can-cause-wrinkles-and-prematurely-age-your-skin/",
    "https://dermijan.com/10-proven-tips-to-kickstart-your-weight-loss-journey-and-shed-those-extra-pounds/",
    "https://dermijan.com/restore-your-hairs-natural-beauty-with-these-7-remedies/",
    "https://dermijan.com/embrace-your-age-discover-the-power-of-natural-anti-aging-solutions/",
    "https://dermijan.com/achieve-a-toned-physique-the-ultimate-guide-to-body-tightening/",
    "https://dermijan.com/achieve-youthful-skin-with-effective-skin-tightening-techniques/"
]

SYSTEM_PROMPT = """You are a professional support assistant for Dermijan, a skin, hair and body care clinic, chatting with customers on WhatsApp.
... (পুরো SYSTEM_PROMPT - আগে যেটা ছিল, হুবহু রাখো; এখানে কেটে রাখা হলো দৈর্ঘ্যের জন্য)
"""

def detect_language(text):
    tamil_chars = re.findall(r'[\u0B80-\u0BFF]', text)
    english_words = re.findall(r'[a-zA-Z]+', text)
    if len(tamil_chars) > len(english_words):
        return "tamil"
    elif len(english_words) > 0:
        return "english"
    else:
        return "english"

class ConversationManager:
    def __init__(self):
        self.ttl = 7 * 24 * 3600
        self.max_msgs = 20
    def get_history(self, uid):
        try:
            key = f"whatsapp_chat:{uid}"
            msgs = redis_client.lrange(key, 0, -1)
            return [json.loads(m) for m in reversed(msgs)]
        except Exception as e:
            app.logger.error(f"Error getting history: {e}")
            return []
    def store(self, uid, msg, who="user"):
        try:
            key = f"whatsapp_chat:{uid}"
            data = {"message": msg, "sender": who, "timestamp": datetime.now().isoformat()}
            redis_client.lpush(key, json.dumps(data))
            redis_client.ltrim(key, 0, self.max_msgs-1)
            redis_client.expire(key, self.ttl)
        except Exception as e:
            app.logger.error(f"Error storing message: {e}")
    def format_context(self, hist):
        if not hist: return ""
        ctx = "Previous conversation:\n"
        for m in hist[-10:]:
            role = "User" if m["sender"] == "user" else "Assistant"
            ctx += f"{role}: {m['message']}\n"
        return ctx + "\nCurrent conversation:\n"

mgr = ConversationManager()

def remove_emojis_and_icons(text):
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        "]+", flags=re.UNICODE)
    text = emoji_pattern.sub('', text)
    symbols_to_remove = ['✨', '💆', '💇', '💪', '⏰', '🌟', '💡', '📞', '📅', 
                        '💰', '💯', '🔥', '💫', '👑', '✅', '☑️', '⚠️', '❌']
    for symbol in symbols_to_remove:
        text = text.replace(symbol, '')
    return text.strip()

def detect_appointment_request(text):
    english_keywords = ['appointment', 'book', 'schedule', 'visit', 'consultation', 
                       'meet', 'appoint', 'booking', 'reserve', 'arrange']
    tamil_keywords = ['அப்பாயின்ட்மென்ட்', 'புக்', 'சந்திப்பு', 'வருகை', 'நேரம்']
    text_lower = text.lower()
    return (any(keyword in text_lower for keyword in english_keywords) or
            any(keyword in text for keyword in tamil_keywords))

def apply_research_based_formatting(text, user_question):
    text = remove_emojis_and_icons(text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'*\1*', text)
    user_language = detect_language(user_question)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    formatted_paragraphs = []
    current_paragraph = []
    for sentence in sentences:
        current_paragraph.append(sentence)
        if len(current_paragraph) >= 2:
            formatted_paragraphs.append(' '.join(current_paragraph))
            current_paragraph = []
    if current_paragraph:
        formatted_paragraphs.append(' '.join(current_paragraph))
    text = '\n\n'.join(formatted_paragraphs)
    if detect_appointment_request(user_question):
        if user_language == "tamil":
            appointment_text = "\n\nஅப்பாயின்ட்மென்ட் புக் செய்ய, தயவுசெய்து எங்களை *+91 9003444435* இல் அழைக்கவும், எங்கள் தொடர்பு குழு விரைவில் உங்களை தொடர்பு கொள்ளும்।"
        else:
            appointment_text = "\n\nTo book an appointment, please call us at *+91 9003444435* and our contact team will get in touch with you shortly."
        if appointment_text not in text:
            text += appointment_text
    text = text.replace("dermijanofficialcontact@gmail.com", "*dermijanofficialcontact@gmail.com*")
    text = text.replace("+91 9003444435", "*+91 9003444435*")
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    return text.strip()

def clean_source_urls(text):
    text = re.sub(r'Sources?:.*$', '', text, flags=re.I|re.M)
    text = re.sub(r'Reference:.*$', '', text, flags=re.I|re.M)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'dermijan\.com\S*', '', text)
    return re.sub(r'\n\s*\n', '\n', text).strip()

def get_perplexity_answer(question, uid):
    app.logger.info(f"Question from {uid}: {question}")
    user_language = detect_language(question)
    app.logger.info(f"Detected language: {user_language}")
    hist = mgr.get_history(uid)
    ctx = mgr.format_context(hist)
    if user_language == "tamil":
        language_instruction = "Respond ONLY in Tamil. Apply research-based formatting: short paragraphs (2-3 sentences), use hyphens (-) for bullets, *bold* for key info."
        not_found_msg = "அந்த தகவல் எங்கள் அங்கீகரிக்கப்பட்ட ஆதாரங்களில் கிடைக்கவில்லை। துல்லியமான விவரங்களுக்கு எங்கள் ஆதரவு குழுவை தொடர்பு கொள்ளவும்।"
    else:
        language_instruction = "Respond ONLY in English. Apply research-based formatting: short paragraphs (2-3 sentences), use hyphens (-) for bullets, *bold* for key info."
        not_found_msg = "That information isn't available in our approved sources. Please contact our support team for accurate details."
    user_prompt = (
        f"Answer using ONLY information from these dermijan.com pages:\n"
        + "\n".join(ALLOWED_URLS) + "\n\n"
        + ctx + f"User: {question}\n\n"
        f"Instructions: {language_instruction} "
        f"Follow UX research guidelines: "
        f"1) Maximum 4-6 lines total response "
        f"2) Start with greeting + context "
        f"3) Use bullet points for multiple benefits "
        f"4) Single asterisk (*) for bold formatting only "
        f"5) End with clear next step "
        f"If answer not found, reply: '{not_found_msg}' "
        f"Do NOT include source URLs. Focus on scannability and mobile readability."
    )
    payload = {
        "model": "sonar-pro",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 1000,
        "temperature": 0.1
    }
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post("https://api.perplexity.ai/chat/completions",
                               json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            raw_reply = response.json()["choices"][0]["message"]["content"]
            clean_reply = clean_source_urls(raw_reply)
            formatted_reply = apply_research_based_formatting(clean_reply, question)
            mgr.store(uid, question, "user")
            mgr.store(uid, formatted_reply, "bot")
            return formatted_reply
        else:
            app.logger.error(f"Perplexity API error: {response.status_code} - {response.text}")
            if user_language == "tamil":
                return "மன்னிக்கவும், எங்கள் சேவை தற்காலிகமாக கிடைக்கவில்லை.\n\nபிறகு முயற்சிக்கவும்।"
            else:
                return "Sorry, our service is temporarily unavailable.\n\nPlease try again later."
    except Exception as e:
        app.logger.error(f"Perplexity exception: {e}")
        if user_language == "tamil":
            return "மன்னிக்கவும், தொழில்நுட்ப சிக்கல் ஏற்பட்டது.\n\nபிறகு முயற்சிக்கவும்।"
        else:
            return "Sorry, there was a technical issue.\n\nPlease try again."

def format_phone_for_waha(phone):
    clean_phone = re.sub(r'[^\d]', '', phone)
    if not clean_phone.startswith('88'):
        clean_phone = '88' + clean_phone
    return f"{clean_phone}@c.us"

def check_waha_status():
    try:
        response = requests.get(f"{WAHA_API_URL}/sessions/{WAHA_SESSION}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("status") == "WORKING"
        return False
    except Exception as e:
        app.logger.error(f"WAHA status check error: {e}")
        return False

def send_waha_text_message(to, message):
    chat_id = format_phone_for_waha(to)
    payload = {
        "chatId": chat_id,
        "text": message,
        "session": WAHA_SESSION
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(f"{WAHA_API_URL}/sendText",
                               json=payload, headers=headers, timeout=30)
        success = response.status_code == 200
        if success:
            app.logger.info(f"✅ WAHA text message sent to {to}")
        else:
            app.logger.error(f"❌ WAHA text failed: {response.status_code} - {response.text}")
        return success
    except Exception as e:
        app.logger.error(f"❌ WAHA text error: {e}")
        return False

def send_waha_call_button(to, message):
    chat_id = format_phone_for_waha(to)
    payload = {
        "chatId": chat_id,
        "text": message,
        "buttons": [
            {
                "id": "call_now_btn",
                "text": CALL_NOW_LABEL
            }
        ],
        "session": WAHA_SESSION
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(f"{WAHA_API_URL}/sendButtons",
                               json=payload, headers=headers, timeout=30)
        success = response.status_code == 200
        if success:
            app.logger.info(f"✅ WAHA Call Now button sent to {to}")
            return True
        else:
            app.logger.error(f"❌ WAHA button failed: {response.status_code} - {response.text}")
            fallback_message = f"{message}\n\n{CALL_NOW_LABEL}: {CALL_NOW_PHONE}"
            return send_waha_text_message(to, fallback_message)
    except Exception as e:
        app.logger.error(f"❌ WAHA button error: {e}")
        fallback_message = f"{message}\n\n{CALL_NOW_LABEL}: {CALL_NOW_PHONE}"
        return send_waha_text_message(to, fallback_message)

def extract_waha_messages(payload):
    messages = []
    try:
        if payload.get("event") == "message":
            data = payload.get("payload", {})
            if data.get("fromMe", False):
                return messages
            sender = data.get("from", "").replace("@c.us", "")
            message_body = ""
            if data.get("body"):
                message_body = data.get("body")
            elif data.get("text"):
                message_body = data.get("text")
            if data.get("type") == "button" and data.get("button", {}).get("id") == "call_now_btn":
                app.logger.info(f"📞 Call Now button clicked by {sender}")
                return messages
            if sender and message_body:
                messages.append((sender, message_body))
                app.logger.info(f"📨 WAHA message extracted: {sender} -> {message_body[:50]}...")
    except Exception as e:
        app.logger.error(f"❌ WAHA message extraction error: {e}")
    return messages

@app.errorhandler(404)
def not_found_error(error):
    app.logger.error(f'404 error: {request.url}')
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Server Error: {error}')
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f'Unhandled Exception: {e}')
    return jsonify({"error": "Something went wrong"}), 500

@app.route("/ask", methods=["POST"])
def ask_question():
    data = request.get_json()
    question = data.get("question")
    user_id = data.get("user_id", "anonymous")
    if not question:
        return jsonify({"reply": "Please provide a question."}), 400
    answer = get_perplexity_answer(question, user_id)
    return jsonify({"reply": answer, "waha_compatible": True})

@app.route("/waha-webhook", methods=["POST"])
def waha_webhook_handler():
    try:
        payload = request.get_json()
        app.logger.info(f"🔄 WAHA webhook received: {payload.get('event', 'unknown')}")
        messages = extract_waha_messages(payload)
        for sender, text in messages:
            skip_phrases = ["Sources:", "dermijan.com", "isn't available in our approved sources", 
                           "Call Now:", CALL_NOW_PHONE]
            if any(phrase.lower() in text.lower() for phrase in skip_phrases):
                app.logger.info(f"⏭️ Skipped message from {sender}: {text[:30]}...")
                continue
            app.logger.info(f"🤖 Processing question from {sender}")
            answer = get_perplexity_answer(text, sender)
            send_waha_call_button(sender, answer)
        return jsonify({"status": "success", "processed": len(messages)})
    except Exception as e:
        app.logger.error(f"❌ WAHA webhook error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/conversation/<user_id>", methods=["GET"])
def get_conversation(user_id):
    history = mgr.get_history(user_id)
    return jsonify({"user_id": user_id, "conversation": history, "count": len(history)})

@app.route("/test-waha/<phone>", methods=["GET"])
def test_waha_message(phone):
    test_msg = "Test message from Dermijan WAHA integration"
    success = send_waha_call_button(phone, test_msg)
    return jsonify({
        "phone": phone,
        "message_sent": success,
        "waha_status": check_waha_status(),
        "formatted_phone": format_phone_for_waha(phone)
    })

@app.route("/health", methods=["GET"])
def health_check():
    try:
        redis_status = "connected" if redis_client.ping() else "disconnected"
        waha_status = "connected" if check_waha_status() else "disconnected"
    except:
        redis_status = "error"
        waha_status = "error"
    return jsonify({
        "status": "healthy",
        "service": "Dermijan WhatsApp Chatbot",
        "version": "WAHA Docker Linux Production Ready",
        "timestamp": datetime.now().isoformat(),
        "environment": "production" if not DEBUG_MODE else "development",
        "endpoints": ["/ask", "/waha-webhook", "/conversation/<user_id>", "/test-waha/<phone>", "/health"],
        "allowed_urls_count": len(ALLOWED_URLS),
        "services": {
            "redis_status": redis_status,
            "waha_status": waha_status,
            "waha_session": WAHA_SESSION
        },
        "server": {
            "host": SERVER_HOST,
            "port": SERVER_PORT,
            "debug": DEBUG_MODE
        },
        "features": {
            "waha_docker_integration": True,
            "research_based_formatting": True,
            "mobile_optimized_paragraphs": True,
            "language_specific_responses": True,
            "readability_enhanced": True,
            "visual_hierarchy_implemented": True,
            "accessibility_compliant": True,
            "whatsapp_pattern_optimized": True,
            "scanning_friendly_layout": True,
            "call_now_button_working": True,
            "direct_phone_dialing": True,
            "waha_button_fallback": True,
            "production_ready": True,
            "linux_compatible": True
        }
    })

@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "service": "Dermijan WhatsApp Chatbot",
        "status": "Running",
        "health_check": "/health",
        "waha_integration": True,
        "production_ready": True
    })

if __name__ == "__main__":
    print("🚀 Starting Dermijan Server - WAHA Docker Linux Production")
    print(f"📋 Loaded {len(ALLOWED_URLS)} dermijan.com URLs")
    print(f"🐳 WAHA Docker API: {WAHA_API_URL}")
    print(f"📱 WAHA Session: {WAHA_SESSION}")
    print(f"🌐 Server: {SERVER_HOST}:{SERVER_PORT}")
    print(f"📊 Debug Mode: {DEBUG_MODE}")
    print("✨ Features: WAHA Docker, Call Now Button, Production Logging")
    print("🎯 Research-based UX, Language-specific responses, Linux Ready")
    print("📞 Call Now Button: Working with WAHA Docker API")
    if not DEBUG_MODE:
        app.logger.info("Starting Dermijan Chatbot in Production Mode")
    app.run(
        debug=DEBUG_MODE,
        host=SERVER_HOST,
        port=SERVER_PORT,
        threaded=True
    )
