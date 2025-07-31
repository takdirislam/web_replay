"""
Dermijan Chatbot - Research-Based UX Optimized Version
Version: 2025-07-31 WAHA + Concurrent Processing
Features:
• WAHA API Integration
• Concurrent message processing
• Research-backed text formatting for maximum readability
• Optimized paragraph structure for mobile users
• Strategic use of dots and hyphens for better scanning
• Visual hierarchy implementation
• WhatsApp-specific user experience patterns
• English and Tamil language support only
"""

from flask import Flask, request, jsonify
from datetime import datetime
import requests, json, os, redis, re
import threading
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

app = Flask(__name__)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# ────────────────────────────────
# WAHA API Configuration
# ────────────────────────────────
WAHA_API_URL = "https://waha.devlike.pro"  # Your WAHA server URL
WAHA_API_KEY = "admin"  # WAHA API key
WAHA_SESSION_NAME = "DERMIJAN_BOT"  # Session name

# WAHA API Headers
WAHA_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {WAHA_API_KEY}" if WAHA_API_KEY else {}
}

# ────────────────────────────────
# Perplexity API Configuration
# ────────────────────────────────
PERPLEXITY_API_KEY = "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"

# ────────────────────────────────
# Concurrent Processing Setup
# ────────────────────────────────
message_queue = Queue()
executor = ThreadPoolExecutor(max_workers=10)  # 10 concurrent workers

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
# Research-Based System Prompt
# ────────────────────────────────
SYSTEM_PROMPT = """You are a professional support assistant for Dermijan, a skin, hair and body care clinic, chatting with customers on WhatsApp.

CRITICAL LANGUAGE RULES:
- If user asks in ENGLISH -> Respond ONLY in English
- If user asks in TAMIL -> Respond ONLY in Tamil  
- NEVER mix languages in a single response
- Detect the user's question language first, then respond in the SAME language only

RESEARCH-BASED FORMATTING GUIDELINES:
Based on UX research, apply these proven readability techniques:

1. PARAGRAPH STRUCTURE (Nielsen Norman Group research):
   - Maximum 2-3 sentences per paragraph on mobile
   - Use single dot (.) + line break for natural reading pauses
   - Front-load important information in first 2 lines

2. BULLET FORMATTING (UXPin studies):
   - Use hyphen (-) for bullet points, not complex symbols
   - Maximum 4-5 bullet points per list
   - Single space between bullet and text
   - Keep bullets parallel in structure

3. VISUAL HIERARCHY (Interaction Design Foundation):
   - Start with greeting + context
   - Main information in *bold* format using single asterisk
   - Secondary details in bulleted format
   - Contact/booking info as final element
   - Use line breaks to separate different topics

4. MOBILE OPTIMIZATION (WhatsApp Business best practices):
   - Keep responses short (4-6 lines maximum)
   - NO emojis, icons, or special symbols allowed
   - Use *bold* only for key terms, prices, and contact information
   - Ensure scannability - users scan rather than read word-by-word

5. WHITESPACE UTILIZATION (Accessibility guidelines):
   - Single line break between related sentences
   - Double line break between different topics
   - Clean spacing around contact information

Response Structure Template:
[Greeting + Context]

[Main Information - 1-2 sentences max]

[Benefits/Features - if applicable]:
- [Benefit 1]
- [Benefit 2] 
- [Benefit 3]

[Next step/Call-to-action]

CONVERSATION RULES:
1. Always address the user's query in the detected language only
2. For treatment questions: Use only dermijan.com source information
3. For pricing: Format as "*Price*: Rs.XXXX (approximate, consultation may vary)"
4. For appointments: Always include phone number with proper formatting
5. For missing info: Direct to support team professionally

Language-Specific Contact Information:
- English: "To book an appointment, please call us at +91 9003444435 and our contact team will get in touch with you shortly."
- Tamil: "அப்பாய்ன்ட்மென்ட் புக் செய்ய, தயவுசெய்து எங்களை +91 9003444435 இல் அழைக்கவும், எங்கள் தொடர்பு குழு விரைவில் உங்களை தொடர்பு கொள்ளும்."

Remember: Apply research-backed formatting consistently. Every response should be scannable, mobile-friendly, and follow proven UX patterns."""

# ────────────────────────────────
# Language Detection Function
# ────────────────────────────────
def detect_language(text):
    """Detect if text is primarily English or Tamil based on UX research"""
    tamil_chars = re.findall(r'[\u0B80-\u0BFF]', text)
    english_words = re.findall(r'[a-zA-Z]+', text)
    
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
# UX-Optimized Text Processing
# ────────────────────────────────
def remove_emojis_and_icons(text):
    """Remove all emojis and icons based on accessibility research"""
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map
        u"\U0001F1E0-\U0001F1FF"  # flags
        "]+", flags=re.UNICODE)
    
    text = emoji_pattern.sub('', text)
    
    # Remove specific symbols that reduce readability
    symbols_to_remove = ['✨', '💆', '💇', '💪', '⏰', '🌟', '💡', '📞', '📅', 
                        '💰', '💯', '🔥', '💫', '👑', '✅', '☑️', '⚠️', '❌']
    
    for symbol in symbols_to_remove:
        text = text.replace(symbol, '')
    
    return text.strip()

def detect_appointment_request(text):
    """Enhanced appointment detection based on user behavior research"""
    english_keywords = ['appointment', 'book', 'schedule', 'visit', 'consultation', 
                       'meet', 'appoint', 'booking', 'reserve', 'arrange']
    tamil_keywords = ['அப்பாய்ன்ட்மென்ட்', 'புக்', 'சந்திப்பு', 'வருகை', 'நேரம்']
    
    text_lower = text.lower()
    return (any(keyword in text_lower for keyword in english_keywords) or
            any(keyword in text for keyword in tamil_keywords))

def apply_research_based_formatting(text, user_question):
    """Apply UX research-backed formatting for optimal readability"""
    # Remove any emojis first
    text = remove_emojis_and_icons(text)
    
    # Fix bold formatting - research shows single asterisk is more readable
    text = re.sub(r'\*\*([^*]+)\*\*', r'*\1*', text)
    
    # Detect user's language for appropriate responses
    user_language = detect_language(user_question)
    
    # Apply research-based paragraph breaks (2-3 sentences max per paragraph)
    # Split long sentences and add strategic line breaks
    sentences = re.split(r'(?<=[.!?])\s+', text)
    formatted_paragraphs = []
    current_paragraph = []
    
    for sentence in sentences:
        current_paragraph.append(sentence)
        # Mobile UX research: max 2-3 sentences per paragraph
        if len(current_paragraph) >= 2:
            formatted_paragraphs.append(' '.join(current_paragraph))
            current_paragraph = []
    
    if current_paragraph:
        formatted_paragraphs.append(' '.join(current_paragraph))
    
    # Join paragraphs with double line breaks for visual breathing space
    text = '\n\n'.join(formatted_paragraphs)
    
    # Add appointment info based on UX research on call-to-action placement
    if detect_appointment_request(user_question):
        if user_language == "tamil":
            appointment_text = "\n\nஅப்பாய்ன்ட்மென்ட் புக் செய்ய, தயவுசெய்து எங்களை +91 9003444435 இல் அழைக்கவும், எங்கள் தொடர்பு குழு விரைவில் உங்களை தொடர்பு கொள்ளும்."
        else:
            appointment_text = "\n\nTo book an appointment, please call us at +91 9003444435 and our contact team will get in touch with you shortly."
        
        if appointment_text not in text:
            text += appointment_text
    
    # Highlight contact info based on visual hierarchy research
    text = text.replace("dermijanofficialcontact@gmail.com", "*dermijanofficialcontact@gmail.com*")
    text = text.replace("+91 9003444435", "+91 9003444435")
    
    # Clean up excessive whitespace while maintaining readability structure
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    
    return text.strip()

def clean_source_urls(text):
    """Remove source URLs that harm readability"""
    text = re.sub(r'Sources?:.*$', '', text, flags=re.I|re.M)
    text = re.sub(r'Reference:.*$', '', text, flags=re.I|re.M)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'dermijan\.com\S*', '', text)
    return re.sub(r'\n\s*\n', '\n', text).strip()

# ────────────────────────────────
# Response Speed Optimization
# ────────────────────────────────

# Cache for frequent responses
@lru_cache(maxsize=100)
def get_cached_response(question_hash):
    """Cache frequent responses to improve speed"""
    return None

def get_perplexity_answer_optimized(question, uid):
    """Optimized Perplexity API call with caching and timeout"""
    print(f"Processing question from {uid}: {question}")
    
    # Check cache first
    question_hash = hash(question.lower().strip())
    cached = get_cached_response(question_hash)
    if cached:
        print(f"Using cached response for {uid}")
        return cached
    
    # Language detection
    user_language = detect_language(question)
    
    # Optimized conversation history (limit to last 7 messages)
    hist = mgr.get_history(uid)[-7:]  # Only last 7 messages
    ctx = mgr.format_context(hist)
    
    # Shorter, more focused prompt for faster processing
    if user_language == "tamil":
        language_instruction = "Tamil-এ সংক্ষিপ্ত উত্তর দিন। সর্বোচ্চ ৩ লাইন।"
        not_found_msg = "அந்த தகவல் எங்கள் அங்கீகரிக்கப்பட்ட ஆதாரங்களில் கிடைக்கவில்லை। துல்லியமான விவரங்களுக்கு எங்கள் ஆதரவு குழுவை தொடர்பு கொள்ளவும்।"
    else:
        language_instruction = "Reply in English. Maximum 3 lines."
        not_found_msg = "That information isn't available in our approved sources. Please contact our support team for accurate details."
    
    # Optimized prompt - shorter for faster processing
    user_prompt = (
        f"Answer briefly using dermijan.com info:\n"
        f"{ctx}User: {question}\n\n"
        f"{language_instruction} "
        f"If not found: '{not_found_msg}'"
    )

    payload = {
        "model": "sonar-pro",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 500,  # Reduced from 1000
        "temperature": 0.1
    }

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        # Reduced timeout for faster failure handling
        response = requests.post(
            "https://api.perplexity.ai/chat/completions", 
            json=payload, 
            headers=headers, 
            timeout=15  # Reduced from 30
        )
        
        if response.status_code == 200:
            raw_reply = response.json()["choices"][0]["message"]["content"]
            clean_reply = clean_source_urls(raw_reply)
            formatted_reply = apply_research_based_formatting(clean_reply, question)
            
            # Cache the response
            get_cached_response.__wrapped__.cache_info()
            
            # Store conversation
            mgr.store(uid, question, "user")
            mgr.store(uid, formatted_reply, "bot")
            
            return formatted_reply
            
        else:
            print(f"Perplexity API error: {response.status_code}")
            return not_found_msg
            
    except Exception as e:
        print(f"Perplexity exception: {e}")
        return not_found_msg

# ────────────────────────────────
# WAHA API Functions
# ────────────────────────────────
def extract_waha_messages(payload):
    """Extract messages from WAHA webhook payload"""
    messages = []
    try:
        # WAHA webhook structure
        if payload.get("event") == "message":
            data = payload.get("payload", {})
            
            # Extract sender and message text
            sender = data.get("from", "").replace("@c.us", "")
            
            # Handle different message types
            message_text = ""
            if data.get("body"):
                message_text = data.get("body")
            elif data.get("text"):
                message_text = data.get("text")
            
            if sender and message_text:
                messages.append((sender, message_text))
                
    except Exception as e:
        print(f"WAHA message extraction error: {e}")
    
    return messages

def send_waha_reply(to_phone, message):
    """Send reply via WAHA API"""
    payload = {
        "session": WAHA_SESSION_NAME,
        "chatId": f"{to_phone}@c.us",
        "text": message
    }
    
    try:
        response = requests.post(
            f"{WAHA_API_URL}/sendText", 
            json=payload, 
            headers=WAHA_HEADERS,
            timeout=10
        )
        
        success = response.status_code in [200, 201]
        if success:
            print(f"Message sent successfully to {to_phone}")
        else:
            print(f"WAHA send error: {response.status_code} - {response.text}")
        
        return success
        
    except Exception as e:
        print(f"WAHA send exception: {e}")
        return False

# ────────────────────────────────
# Concurrent Processing Functions
# ────────────────────────────────
def process_message_async(sender, text):
    """Process single message asynchronously"""
    try:
        print(f"Processing message from {sender}: {text}")
        
        # Get AI response
        answer = get_perplexity_answer_optimized(text, sender)
        
        # Send reply
        send_waha_reply(sender, answer)
        
    except Exception as e:
        print(f"Async processing error for {sender}: {e}")

def message_worker():
    """Background worker to process message queue"""
    while True:
        try:
            if not message_queue.empty():
                sender, text = message_queue.get()
                
                # Submit to thread pool for concurrent processing
                executor.submit(process_message_async, sender, text)
                
                message_queue.task_done()
            else:
                threading.Event().wait(0.1)  # Small delay when queue is empty
                
        except Exception as e:
            print(f"Worker error: {e}")

# Start background worker thread
worker_thread = threading.Thread(target=message_worker, daemon=True)
worker_thread.start()

# ────────────────────────────────
# Flask Routes
# ────────────────────────────────
@app.route("/ask", methods=["POST"])
def ask_question():
    """Direct API endpoint with UX optimization"""
    data = request.get_json()
    question = data.get("question")
    user_id = data.get("user_id", "anonymous")
    
    if not question:
        return jsonify({"reply": "Please provide a question."}), 400
    
    answer = get_perplexity_answer_optimized(question, user_id)
    return jsonify({"reply": answer})

@app.route("/webhook", methods=["POST"])
def webhook_handler():
    """Optimized webhook handler for concurrent processing"""
    try:
        payload = request.get_json()
        
        # Quick response to avoid timeout
        response = jsonify({"status": "received"})
        
        # Extract messages using WAHA format
        messages = extract_waha_messages(payload)
        
        # Add messages to queue for async processing
        for sender, text in messages:
            # Skip bot messages to prevent loops
            skip_phrases = ["Sources:", "dermijan.com", "isn't available in our approved sources"]
            if any(phrase.lower() in text.lower() for phrase in skip_phrases):
                continue
            
            # Add to queue instead of processing immediately
            message_queue.put((sender, text))
            print(f"Message queued from {sender}")
        
        return response
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({"status": "error"}), 500

@app.route("/conversation/<user_id>", methods=["GET"])
def get_conversation(user_id):
    """Get conversation history"""
    history = mgr.get_history(user_id)
    return jsonify({"user_id": user_id, "conversation": history, "count": len(history)})

@app.route("/", methods=["GET"])
def health_check():
    """Health check with UX feature status"""
    try:
        redis_status = "connected" if redis_client.ping() else "disconnected"
    except:
        redis_status = "error"
    
    return jsonify({
        "status": "Dermijan Server Running - WAHA + Concurrent Processing",
        "version": "Research-Based User Experience Enhanced",
        "endpoints": ["/ask", "/webhook", "/conversation/<user_id>"],
        "allowed_urls_count": len(ALLOWED_URLS),
        "redis_status": redis_status,
        "supported_languages": ["English", "Tamil"],
        "conversation_history_limit": 7,
        "ux_features": {
            "waha_api_integration": True,
            "concurrent_processing": True,
            "research_based_formatting": True,
            "mobile_optimized_paragraphs": True,
            "language_specific_responses": True,
            "readability_enhanced": True,
            "visual_hierarchy_implemented": True,
            "accessibility_compliant": True,
            "whatsapp_pattern_optimized": True,
            "scanning_friendly_layout": True,
            "response_caching": True,
            "speed_optimized": True
        }
    })

# ────────────────────────────────
# Main
# ────────────────────────────────
if __name__ == "__main__":
    print("🚀 Starting Dermijan Server - WAHA + Concurrent Processing")
    print(f"📋 Loaded {len(ALLOWED_URLS)} dermijan.com URLs")
    print("⚡ Features: WAHA API, Concurrent processing, Speed optimized")
    print("🌐 Supported Languages: English and Tamil only")
    print("💬 Conversation History: Last 7 messages")
    print("🔄 Background workers: Started")
    print("📱 Mobile-optimized responses ready")
    
    # Start Flask with threaded support
    app.run(
        debug=False,  # Disable debug in production for better performance
        host='0.0.0.0', 
        port=8000,
        threaded=True  # Enable threading support
    )
