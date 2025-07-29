"""
Dermijan Chatbot - Language Specific Responses
Version: 2025-07-29 Final Update
Features:
• Language detection: English question -> English response, Tamil question -> Tamil response
• No language mixing allowed
• Single asterisk (*) for bold formatting
• Professional format without emojis
"""

from flask import Flask, request, jsonify
from datetime import datetime
import requests, json, os, redis, re

app = Flask(__name__)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# ────────────────────────────────
# API Configuration
# ────────────────────────────────
PERPLEXITY_API_KEY = "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"
WASENDER_API_TOKEN = "37bf33ac1d6e4e6be8ae324373c2171400a1dd6183c6e501df646eb5f436ef6f"
WASENDER_SESSION = "TAKDIR"
WASENDER_API_URL = "https://wasenderapi.com/api/send-message"

# ────────────────────────────────
# Dermijan URLs (unchanged)
# ────────────────────────────────
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

# ────────────────────────────────
# System Prompt (Language Specific)
# ────────────────────────────────
SYSTEM_PROMPT = """You are a support assistant for Dermijan, a skin, hair and body care clinic, chatting with customers on WhatsApp.

CRITICAL LANGUAGE RULES:
- If user asks in ENGLISH -> Respond ONLY in English
- If user asks in TAMIL -> Respond ONLY in Tamil  
- NEVER mix languages in a single response
- Detect the user's question language first, then respond in the SAME language only

Guidelines:
- Use simple and natural language (not overly professional)
- NO emojis, icons, or special symbols allowed
- Use single asterisk (*) for bold formatting: *important text*
- Use hyphens (-) for bullet points
- Keep replies short and friendly (4-6 lines maximum)
- Line breaks for better readability

Response Rules:
1. Always address the user's query clearly in the SAME language they used
2. For treatment or service questions:
   - Use only information from provided dermijan.com sources
   - If info unavailable:
     * English: "That specific detail isn't available right now. Please contact our support team at *dermijanofficialcontact@gmail.com* or *+91 9003444435* for accurate information."
     * Tamil: "அந்த குறிப்பிட்ட விவரம் இப்போது கிடைக்கவில்லை. துல்லியமான தகவலுக்கு எங்கள் ஆதரவு குழுவை *dermijanofficialcontact@gmail.com* அல்லது *+91 9003444435* இல் தொடர்பு கொள்ளவும்."
3. For pricing questions:
   - If known: "*Price*: Rs.XXXX (approximate, may vary based on consultation)"
   - If unknown: Contact support message in user's language
4. For appointment/booking requests:
   - English: "To book an appointment, please call us at *+91 9003444435* and our contact team will get in touch with you shortly."
   - Tamil: "அப்பாய்ன்ட்மென்ட் புக் செய்ய, தயவுசெய்து எங்களை *+91 9003444435* இல் அழைக்கவும், எங்கள் தொடர்பு குழு விரைவில் உங்களை தொடர்பு கொள்ளும்."
5. For skin/hair/body issues:
   - Ask follow-up questions in user's language to understand the concern better

Remember: STRICT language separation - English questions get English responses, Tamil questions get Tamil responses."""

# ────────────────────────────────
# Language Detection Function
# ────────────────────────────────
def detect_language(text):
    """Detect if text is primarily English or Tamil"""
    # Tamil Unicode range detection
    tamil_chars = re.findall(r'[\u0B80-\u0BFF]', text)
    english_words = re.findall(r'[a-zA-Z]+', text)
    
    # Simple detection logic
    if len(tamil_chars) > len(english_words):
        return "tamil"
    elif len(english_words) > 0:
        return "english"
    else:
        return "english"  # default to English

# ────────────────────────────────
# Conversation Manager
# ────────────────────────────────
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
            print("Error getting history:", e)
            return []

    def store(self, uid, msg, who="user"):
        try:
            key = f"whatsapp_chat:{uid}"
            data = {"message": msg, "sender": who, "timestamp": datetime.now().isoformat()}
            redis_client.lpush(key, json.dumps(data))
            redis_client.ltrim(key, 0, self.max_msgs-1)
            redis_client.expire(key, self.ttl)
        except Exception as e:
            print("Error storing message:", e)

    def format_context(self, hist):
        if not hist: return ""
        ctx = "Previous conversation:\n"
        for m in hist[-10:]:
            role = "User" if m["sender"] == "user" else "Assistant"
            ctx += f"{role}: {m['message']}\n"
        return ctx + "\nCurrent conversation:\n"

mgr = ConversationManager()

# ────────────────────────────────
# Text Processing Functions
# ────────────────────────────────
def remove_emojis_and_icons(text):
    """Remove all emojis, icons and special symbols"""
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map
        u"\U0001F1E0-\U0001F1FF"  # flags
        "]+", flags=re.UNICODE)
    
    text = emoji_pattern.sub('', text)
    
    # Remove specific symbols
    symbols_to_remove = ['✨', '💆', '💇', '💪', '⏰', '🌟', '💡', '📞', '📅', 
                        '💰', '💯', '🔥', '💫', '👑', '✅', '☑️', '⚠️', '❌']
    
    for symbol in symbols_to_remove:
        text = text.replace(symbol, '')
    
    return text.strip()

def detect_appointment_request(text):
    """Check if user is requesting appointment/booking"""
    english_keywords = ['appointment', 'book', 'schedule', 'visit', 'consultation', 
                       'meet', 'appoint', 'booking', 'reserve']
    tamil_keywords = ['அப்பாய்ன்ட்மென்ட்', 'புக்', 'சந்திப்பு', 'வருகை']
    
    text_lower = text.lower()
    return (any(keyword in text_lower for keyword in english_keywords) or
            any(keyword in text for keyword in tamil_keywords))

def fix_bold_formatting(text):
    """Convert double asterisks to single asterisks for bold"""
    # Replace **text** with *text*
    text = re.sub(r'\*\*([^*]+)\*\*', r'*\1*', text)
    return text

def format_professional_response(reply, user_question):
    """Format response professionally without emojis"""
    # Remove any emojis
    reply = remove_emojis_and_icons(reply)
    
    # Fix bold formatting (** -> *)
    reply = fix_bold_formatting(reply)
    
    # Detect user's language
    user_language = detect_language(user_question)
    
    # Add appointment info if requested
    if detect_appointment_request(user_question):
        if user_language == "tamil":
            appointment_text = "\n\nஅப்பாய்ன்ட்மென்ட் புக் செய்ய, தயவுசெய்து எங்களை *+91 9003444435* இல் அழைக்கவும், எங்கள் தொடர்பு குழு விரைவில் உங்களை தொடர்பு கொள்ளும்."
        else:
            appointment_text = "\n\nTo book an appointment, please call us at *+91 9003444435* and our contact team will get in touch with you shortly."
        
        if appointment_text not in reply:
            reply += appointment_text
    
    # Clean up formatting
    reply = reply.replace(". ", ".\n\n")
    
    # Highlight contact info with single asterisk
    reply = reply.replace("dermijanofficialcontact@gmail.com", "*dermijanofficialcontact@gmail.com*")
    reply = reply.replace("+91 9003444435", "*+91 9003444435*")
    
    # Remove extra whitespace
    reply = re.sub(r'\n\s*\n\s*\n', '\n\n', reply)
    
    return reply.strip()

def clean_source_urls(text):
    """Remove source URLs and references"""
    text = re.sub(r'Sources?:.*$', '', text, flags=re.I|re.M)
    text = re.sub(r'Reference:.*$', '', text, flags=re.I|re.M)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'dermijan\.com\S*', '', text)
    return re.sub(r'\n\s*\n', '\n', text).strip()

# ────────────────────────────────
# Perplexity API
# ────────────────────────────────
def get_perplexity_answer(question, uid):
    """Get answer from Perplexity API with language detection"""
    print(f"Question from {uid}: {question}")
    
    # Detect user's language
    user_language = detect_language(question)
    print(f"Detected language: {user_language}")
    
    hist = mgr.get_history(uid)
    ctx = mgr.format_context(hist)
    
    # Language-specific instructions
    if user_language == "tamil":
        language_instruction = "Respond ONLY in Tamil language. Do not use any English words."
        not_found_msg = "அந்த தகவல் எங்கள் அங்கீகரிக்கப்பட்ட ஆதாரங்களில் கிடைக்கவில்லை. துல்லியமான விவரங்களுக்கு எங்கள் ஆதரவு குழுவை தொடர்பு கொள்ளவும்."
    else:
        language_instruction = "Respond ONLY in English language. Do not use any Tamil words."
        not_found_msg = "That information isn't available in our approved sources. Please contact our support team for accurate details."
    
    user_prompt = (
        f"Answer using ONLY information from these dermijan.com pages:\n"
        + "\n".join(ALLOWED_URLS) + "\n\n"
        + ctx + f"User: {question}\n\n"
        f"Instructions: {language_instruction} "
        f"Give a SHORT answer (4-6 lines max). "
        f"Use single asterisk (*) for bold formatting. NO emojis or icons allowed. "
        f"If answer not found, reply: '{not_found_msg}' "
        f"Do NOT include source URLs in your response."
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
            formatted_reply = format_professional_response(clean_reply, question)
            
            # Store conversation
            mgr.store(uid, question, "user")
            mgr.store(uid, formatted_reply, "bot")
            
            return formatted_reply
        else:
            print(f"Perplexity API error: {response.status_code} - {response.text}")
            if user_language == "tamil":
                return "மன்னிக்கவும், எங்கள் சேவை தற்காலிகமாக கிடைக்கவில்லை. பிறகு முயற்சிக்கவும்."
            else:
                return "Sorry, our service is temporarily unavailable. Please try again later."
            
    except Exception as e:
        print(f"Perplexity exception: {e}")
        if user_language == "tamil":
            return "மன்னிக்கவும், தொழில்நுட்ப சிக்கல் ஏற்பட்டது. பிறகு முயற்சிக்கவும்."
        else:
            return "Sorry, there was a technical issue. Please try again."

# ────────────────────────────────
# WASender Functions (unchanged)
# ────────────────────────────────
def extract_wasender_messages(payload):
    """Extract messages from WASender webhook"""
    messages = []
    try:
        if payload.get("event") == "messages.upsert":
            data = payload.get("data", {}).get("messages", {})
            sender = data.get("key", {}).get("remoteJid", "").replace("@s.whatsapp.net", "").replace("+", "")
            
            message_content = data.get("message", {})
            text = ""
            if "conversation" in message_content:
                text = message_content["conversation"]
            elif "extendedTextMessage" in message_content:
                text = message_content["extendedTextMessage"].get("text", "")
            
            if sender and text:
                messages.append((sender, text))
                
    except Exception as e:
        print(f"Message extraction error: {e}")
    
    return messages

def send_wasender_reply(to_phone, message):
    """Send reply via WASender API"""
    if not WASENDER_API_TOKEN:
        print("WASender API token missing")
        return False
    
    payload = {
        "session": WASENDER_SESSION,
        "to": to_phone,
        "text": message
    }
    
    headers = {
        "Authorization": f"Bearer {WASENDER_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(WASENDER_API_URL, json=payload, headers=headers)
        success = response.status_code in [200, 201]
        print("Message sent successfully" if success else f"Send error: {response.status_code}")
        return success
    except Exception as e:
        print(f"Send error: {e}")
        return False

# ────────────────────────────────
# Flask Routes (unchanged)
# ────────────────────────────────
@app.route("/ask", methods=["POST"])
def ask_question():
    """Direct API endpoint"""
    data = request.get_json()
    question = data.get("question")
    user_id = data.get("user_id", "anonymous")
    
    if not question:
        return jsonify({"reply": "Please provide a question."}), 400
    
    answer = get_perplexity_answer(question, user_id)
    return jsonify({"reply": answer})

@app.route("/webhook", methods=["POST"])
def webhook_handler():
    """WhatsApp webhook handler"""
    try:
        payload = request.get_json()
        messages = extract_wasender_messages(payload)
        
        for sender, text in messages:
            # Skip bot messages to prevent loops
            skip_phrases = ["Sources:", "dermijan.com", "isn't available in our approved sources"]
            if any(phrase.lower() in text.lower() for phrase in skip_phrases):
                continue
            
            answer = get_perplexity_answer(text, sender)
            send_wasender_reply(sender, answer)
        
        return jsonify({"status": "success"})
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/conversation/<user_id>", methods=["GET"])
def get_conversation(user_id):
    """Get conversation history"""
    history = mgr.get_history(user_id)
    return jsonify({"user_id": user_id, "conversation": history, "count": len(history)})

@app.route("/", methods=["GET"])
def health_check():
    """Health check endpoint"""
    try:
        redis_status = "connected" if redis_client.ping() else "disconnected"
    except:
        redis_status = "error"
    
    return jsonify({
        "status": "Dermijan Server Running",
        "version": "Language Specific Responses",
        "endpoints": ["/ask", "/webhook", "/conversation/<user_id>"],
        "allowed_urls_count": len(ALLOWED_URLS),
        "redis_status": redis_status,
        "features": {
            "language_detection": True,
            "english_only_responses": True,
            "tamil_only_responses": True,
            "single_asterisk_bold": True,
            "emoji_free": True,
            "appointment_handling": True
        }
    })

# ────────────────────────────────
# Main
# ────────────────────────────────
if __name__ == "__main__":
    print("🚀 Starting Dermijan Server (Language Specific)")
    print(f"📋 Loaded {len(ALLOWED_URLS)} dermijan.com URLs")
    print("🔗 Features: English->English, Tamil->Tamil, Single * bold")
    print("✨ No language mixing, Professional format")
    app.run(debug=True, host='0.0.0.0', port=8000)
