from flask import Flask, request, jsonify
from datetime import datetime
import requests, json, os, redis, re

app = Flask(__name__)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# ────────────────────────────────
# WAHA API Configuration
# ────────────────────────────────
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "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")

# WAHA Configuration
WAHA_BASE_URL = os.getenv("WAHA_BASE_URL", "http://localhost:3000")  # Your WAHA server URL
WAHA_API_KEY = os.getenv("WAHA_API_KEY", "your-waha-api-key")  # If authentication required

# Multiple Session Management
ACTIVE_SESSIONS = {}  # Store active sessions
DEFAULT_SESSION = "default"

# ────────────────────────────────
# Multiple User Session Manager
# ────────────────────────────────
class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.load_sessions_from_redis()
    
    def load_sessions_from_redis(self):
        """Load active sessions from Redis"""
        try:
            sessions_data = redis_client.get("waha_active_sessions")
            if sessions_data:
                self.sessions = json.loads(sessions_data)
                print(f"Loaded {len(self.sessions)} active sessions")
        except Exception as e:
            print(f"Error loading sessions: {e}")
    
    def save_sessions_to_redis(self):
        """Save active sessions to Redis"""
        try:
            redis_client.set("waha_active_sessions", json.dumps(self.sessions))
        except Exception as e:
            print(f"Error saving sessions: {e}")
    
    def add_session(self, session_name, config=None):
        """Add new session"""
        self.sessions[session_name] = {
            "name": session_name,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "config": config or {},
            "message_count": 0
        }
        self.save_sessions_to_redis()
        return True
    
    def get_session(self, session_name):
        """Get session info"""
        return self.sessions.get(session_name)
    
    def get_all_sessions(self):
        """Get all sessions"""
        return self.sessions
    
    def remove_session(self, session_name):
        """Remove session"""
        if session_name in self.sessions:
            del self.sessions[session_name]
            self.save_sessions_to_redis()
            return True
        return False
    
    def get_session_for_user(self, user_phone):
        """Get appropriate session for user"""
        # Simple routing - can be enhanced based on business logic
        user_session_key = f"user_session:{user_phone}"
        assigned_session = redis_client.get(user_session_key)
        
        if assigned_session and assigned_session in self.sessions:
            return assigned_session
        else:
            # Assign to default or least loaded session
            if self.sessions:
                # Find session with least messages
                least_loaded = min(self.sessions.items(), 
                                 key=lambda x: x[1].get("message_count", 0))
                session_name = least_loaded[0]
            else:
                session_name = DEFAULT_SESSION
                self.add_session(DEFAULT_SESSION)
            
            # Store assignment
            redis_client.setex(user_session_key, 86400, session_name)  # 24 hours
            return session_name
    
    def increment_message_count(self, session_name):
        """Increment message count for session"""
        if session_name in self.sessions:
            self.sessions[session_name]["message_count"] += 1
            self.save_sessions_to_redis()

session_manager = SessionManager()

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
- English: "To book an appointment, please call us at *+91 9003444435* and our contact team will get in touch with you shortly."
- Tamil: "அப்பாய்ன்ட்மென்ட் புக் செய்ய, தயவுசெய்து எங்களை *+91 9003444435* இல் அழைக்கவும், எங்கள் தொடர்பু குழু விরைவில் உங்களை தொடர்பு கொள்ளும்।"

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
            appointment_text = "\n\nஅப்பாய்ன்ட்மென்ட் புக் செய்ய, தயவுசெய்து எங்களை *+91 9003444435* இல் அழைக்கவும், எங்கள் தொடர்பு குழு விரைவில் உங்களை தொடர்பு கொள்ளும்।"
        else:
            appointment_text = "\n\nTo book an appointment, please call us at *+91 9003444435* and our contact team will get in touch with you shortly."
        
        if appointment_text not in text:
            text += appointment_text
    
    # Highlight contact info based on visual hierarchy research
    text = text.replace("dermijanofficialcontact@gmail.com", "*dermijanofficialcontact@gmail.com*")
    text = text.replace("+91 9003444435", "*+91 9003444435*")
    
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
# Enhanced Perplexity API Integration
# ────────────────────────────────
def get_perplexity_answer(question, uid):
    """Get UX-optimized answer from Perplexity API"""
    print(f"Question from {uid}: {question}")
    
    # Language detection for appropriate response
    user_language = detect_language(question)
    print(f"Detected language: {user_language}")
    
    hist = mgr.get_history(uid)
    ctx = mgr.format_context(hist)
    
    # Research-based language instructions
    if user_language == "tamil":
        language_instruction = "Respond ONLY in Tamil. Apply research-based formatting: short paragraphs (2-3 sentences), use hyphens (-) for bullets, *bold* for key info."
        not_found_msg = "அந்த தகவல் எங்கள் அங்கீகரிக்கப்பட்ட ஆதாரங்களில் கிடைக்கவில்லை. துல்லியமான விவரங்களுக்கு எங்கள் ஆதரவு குழுவை தொடர்பு கொள்ளவும்।"
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
            
            # Store conversation with research-based formatting
            mgr.store(uid, question, "user")
            mgr.store(uid, formatted_reply, "bot")
            
            return formatted_reply
        else:
            print(f"Perplexity API error: {response.status_code} - {response.text}")
            if user_language == "tamil":
                return "மன்னிக்கவும், எங்கள் சேவை தற்காலிகமாக கிடைக்கவில்லை.\n\nபிறகு முயற்சிக்கவும்।"
            else:
                return "Sorry, our service is temporarily unavailable.\n\nPlease try again later."
            
    except Exception as e:
        print(f"Perplexity exception: {e}")
        if user_language == "tamil":
            return "மன்னிக்கவும், தொழில்நுட்ப சிக்கல் ஏற்பட்டது.\n\nபிறகு முயற்சிக்கவும்।"
        else:
            return "Sorry, there was a technical issue.\n\nPlease try again."

# ────────────────────────────────
# WAHA Functions
# ────────────────────────────────
def extract_waha_messages(payload):
    """Extract messages from WAHA webhook"""
    messages = []
    try:
        # WAHA webhook format
        if payload.get("event") == "message":
            session = payload.get("session", DEFAULT_SESSION)
            data = payload.get("payload", {})
            
            # Extract sender
            sender = data.get("from", "")
            if "@c.us" in sender:
                sender = sender.replace("@c.us", "")
            
            # Extract message content
            text = ""
            if data.get("type") == "chat":
                text = data.get("body", "")
            elif data.get("type") == "text":
                text = data.get("text", {}).get("body", "")
            
            if sender and text:
                messages.append((sender, text, session))
                print(f"Message from {sender} in session {session}: {text[:50]}...")
                
    except Exception as e:
        print(f"Message extraction error: {e}")
    
    return messages

def send_waha_reply(to_phone, message, session_name=None):
    """Send UX-optimized reply via WAHA API"""
    if not session_name:
        session_name = session_manager.get_session_for_user(to_phone)
    
    # Prepare phone number for WAHA
    phone = to_phone.replace("+", "")
    if not phone.endswith("@c.us"):
        phone = f"{phone}@c.us"
    
    # WAHA send message endpoint
    url = f"{WAHA_BASE_URL}/api/sendText"
    
    payload = {
        "session": session_name,
        "chatId": phone,
        "text": message
    }
    
    headers = {"Content-Type": "application/json"}
    if WAHA_API_KEY and WAHA_API_KEY != "your-waha-api-key":
        headers["Authorization"] = f"Bearer {WAHA_API_KEY}"
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        success = response.status_code in [200, 201]
        
        if success:
            print(f"Message sent successfully via session {session_name}")
            session_manager.increment_message_count(session_name)
        else:
            print(f"Send error: {response.status_code} - {response.text}")
        
        return success
    except Exception as e:
        print(f"Send error: {e}")
        return False

def get_waha_sessions():
    """Get all WAHA sessions from server"""
    try:
        url = f"{WAHA_BASE_URL}/api/sessions"
        headers = {}
        if WAHA_API_KEY and WAHA_API_KEY != "your-waha-api-key":
            headers["Authorization"] = f"Bearer {WAHA_API_KEY}"
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting WAHA sessions: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error getting WAHA sessions: {e}")
        return []

def start_waha_session(session_name):
    """Start a new WAHA session"""
    try:
        url = f"{WAHA_BASE_URL}/api/sessions/start"
        payload = {"name": session_name}
        headers = {"Content-Type": "application/json"}
        if WAHA_API_KEY and WAHA_API_KEY != "your-waha-api-key":
            headers["Authorization"] = f"Bearer {WAHA_API_KEY}"
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        success = response.status_code in [200, 201]
        
        if success:
            session_manager.add_session(session_name)
            print(f"WAHA session {session_name} started successfully")
        
        return success, response.json() if success else response.text
    except Exception as e:
        print(f"Error starting WAHA session: {e}")
        return False, str(e)

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
    
    answer = get_perplexity_answer(question, user_id)
    return jsonify({"reply": answer})

@app.route("/webhook", methods=["POST"])
def webhook_handler():
    """WAHA webhook handler with multiple user support"""
    try:
        payload = request.get_json()
        messages = extract_waha_messages(payload)
        
        for sender, text, session in messages:
            # Skip bot messages to prevent loops
            skip_phrases = ["Sources:", "dermijan.com", "isn't available in our approved sources"]
            if any(phrase.lower() in text.lower() for phrase in skip_phrases):
                continue
            
            print(f"Processing message from {sender} in session {session}: {text}")
            answer = get_perplexity_answer(text, sender)
            send_waha_reply(sender, answer, session)
        
        return jsonify({"status": "success", "processed": len(messages)})
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/conversation/<user_id>", methods=["GET"])
def get_conversation(user_id):
    """Get conversation history"""
    history = mgr.get_history(user_id)
    return jsonify({"user_id": user_id, "conversation": history, "count": len(history)})

# ────────────────────────────────
# Multiple User Management Routes
# ────────────────────────────────
@app.route("/sessions", methods=["GET"])
def list_sessions():
    """List all active sessions"""
    waha_sessions = get_waha_sessions()
    managed_sessions = session_manager.get_all_sessions()
    
    return jsonify({
        "waha_sessions": waha_sessions,
        "managed_sessions": managed_sessions,
        "total_managed": len(managed_sessions)
    })

@app.route("/sessions/<session_name>", methods=["POST"])
def create_session(session_name):
    """Create new session"""
    success, result = start_waha_session(session_name)
    
    if success:
        return jsonify({
            "status": "success",
            "message": f"Session {session_name} created successfully",
            "session_info": result
        })
    else:
        return jsonify({
            "status": "error",
            "message": f"Failed to create session {session_name}",
            "error": result
        }), 500

@app.route("/sessions/<session_name>", methods=["DELETE"])
def remove_session(session_name):
    """Remove session"""
    removed = session_manager.remove_session(session_name)
    
    if removed:
        return jsonify({
            "status": "success",
            "message": f"Session {session_name} removed successfully"
        })
    else:
        return jsonify({
            "status": "error",
            "message": f"Session {session_name} not found"
        }), 404

@app.route("/users/<user_phone>/session", methods=["GET"])
def get_user_session(user_phone):
    """Get assigned session for user"""
    session_name = session_manager.get_session_for_user(user_phone)
    session_info = session_manager.get_session(session_name)
    
    return jsonify({
        "user_phone": user_phone,
        "assigned_session": session_name,
        "session_info": session_info
    })

@app.route("/users/<user_phone>/session", methods=["POST"])
def assign_user_session(user_phone):
    """Assign specific session to user"""
    data = request.get_json()
    session_name = data.get("session_name")
    
    if not session_name:
        return jsonify({"error": "session_name required"}), 400
    
    if session_name not in session_manager.sessions:
        return jsonify({"error": "Session not found"}), 404
    
    # Store assignment
    user_session_key = f"user_session:{user_phone}"
    redis_client.setex(user_session_key, 86400, session_name)
    
    return jsonify({
        "status": "success",
        "message": f"User {user_phone} assigned to session {session_name}"
    })

@app.route("/", methods=["GET"])
def health_check():
    """Health check with multiple user support status"""
    try:
        redis_status = "connected" if redis_client.ping() else "disconnected"
    except:
        redis_status = "error"
    
    waha_sessions = get_waha_sessions()
    managed_sessions = session_manager.get_all_sessions()
    
    return jsonify({
        "status": "Dermijan Server Running - UX Optimized with WAHA Multiple User Support",
        "version": "Research-Based User Experience Enhanced + WAHA API + Multi-User",
        "endpoints": [
            "/ask", "/webhook", "/conversation/<user_id>", 
            "/sessions", "/sessions/<name>", "/users/<phone>/session"
        ],
        "allowed_urls_count": len(ALLOWED_URLS),
        "redis_status": redis_status,
        "waha_integration": {
            "base_url": WAHA_BASE_URL,
            "api_key_configured": WAHA_API_KEY != "your-waha-api-key",
            "active_waha_sessions": len(waha_sessions),
            "managed_sessions": len(managed_sessions)
        },
        "multi_user_features": {
            "session_management": True,
            "user_assignment": True,
            "load_balancing": True,
            "session_monitoring": True
        },
        "ux_features": {
            "research_based_formatting": True,
            "mobile_optimized_paragraphs": True,
            "language_specific_responses": True,
            "readability_enhanced": True,
            "visual_hierarchy_implemented": True,
            "accessibility_compliant": True,
            "whatsapp_pattern_optimized": True,
            "scanning_friendly_layout": True
        }
    })

# ────────────────────────────────
# Main
# ────────────────────────────────
if __name__ == "__main__":
    # Initialize default session if none exist
    if not session_manager.sessions:
        session_manager.add_session(DEFAULT_SESSION)
        print(f"Created default session: {DEFAULT_SESSION}")
    
    print("🚀 Starting Dermijan Server - UX Research Enhanced with WAHA Multi-User Support")
    print(f"📋 Loaded {len(ALLOWED_URLS)} dermijan.com URLs")
    print("🎯 Features: Research-based formatting, Mobile-optimized, Visual hierarchy")
    print("✨ UX Enhancements: Short paragraphs, Strategic dots/hyphens, Scannable layout")
    print("📱 Mobile-first readability, Language-specific responses, Accessibility compliant")
    print("🔗 WAHA Integration: Multiple sessions, User assignment, Load balancing")
    print(f"🌐 WAHA Server: {WAHA_BASE_URL}")
    print(f"📊 Active Sessions: {len(session_manager.sessions)}")
    
    app.run(debug=True, host='0.0.0.0', port=8000)
