from flask import Flask, request, jsonify
from datetime import datetime
import requests, json, os, redis, re

app = Flask(__name__)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# ────────────────────────────────
# API Configuration - DYNAMIC WAHA URL
# ────────────────────────────────
PERPLEXITY_API_KEY = "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"

# Dynamic WAHA URL - Environment variable দিয়ে control করা হবে
WAHA_BASE_URL = os.getenv("WAHA_BASE_URL", "http://localhost:3000")
WAHA_SESSION = os.getenv("WAHA_SESSION", "WAHA")
WAHA_SEND_TEXT_URL = f"{WAHA_BASE_URL}/api/sendText"

# Debug info
print(f"🔗 WAHA Configuration: {WAHA_BASE_URL} (Session: {WAHA_SESSION})")

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
- Tamil: "அப்பாய்ன்ட்மென்ট் புக் செய்ய, தயவுசெய்து எங்களை +91 9003444435 இல் அழைக்கவும், எங்கள் தொடர்பு குழு விরைவில் உங்களை தொடর்பு கொள்ளும்।"

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
    tamil_keywords = ['அப்பாய்ன্ট্মেন্ট্', 'পুক্', 'சந্திप্পু', 'বরুকৈ', 'নেরম্']
    
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
            appointment_text = "\n\nअप्पायन्ट्मेन्ट् পুক্ সেয়য, তযবুসেয়তু এল্লালে +91 9003444435 ইল অলয়ক্কবুল, এল্লাল তোদর্পু কুজু বিরেবিল উল্লালৈ তোদর্পু কোল্লুম্।"
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
        not_found_msg = "அন্ত তকবল এল্লাল অল্লীকরিক্কপ্পট্ট আতারল্লালিল কিদাইক্কবিল্লাই। তুল্লিযমান বিবরল্লালুক্ক এল্লাল আতরবু কুজুবৈ তোদর্পু কোল্লবুম্।"
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
                return "মন্নিক্কবুম্, এল্লাল সেবৈ তর্কালিকমাক কিদাইক্কবিল্লাই.\n\nপিরকু মুযরসিক্কবুম্।"
            else:
                return "Sorry, our service is temporarily unavailable.\n\nPlease try again later."
            
    except Exception as e:
        print(f"Perplexity exception: {e}")
        if user_language == "tamil":
            return "মন্নিক্কবুম্, তোজিল্নুটপ সিক্কল এরপট্টতু.\n\nপিরকু মুযরসিক্কবুম্।"
        else:
            return "Sorry, there was a technical issue.\n\nPlease try again."

# ────────────────────────────────
# WAHA Functions - ENHANCED WITH CONNECTION RECOVERY
# ────────────────────────────────
def extract_waha_messages(payload):
    """Extract messages from WAHA webhook - FINAL FIX FOR CURRENT STRUCTURE"""
    messages = []
    try:
        print(f"🔍 WAHA webhook received: {json.dumps(payload, indent=2)}")
        
        # Handle the current WAHA payload structure
        if payload.get("event") == "message":
            # Message data is directly in payload
            data = payload.get("payload", {})
            
            # Extract sender from 'from' field
            sender = ""
            if "from" in data:
                sender = data["from"].replace("@c.us", "").replace("@s.whatsapp.net", "")
                # Remove country code for Bangladesh numbers
                if sender.startswith("880"):
                    sender = sender[3:]  # Remove 880 prefix
            
            # Extract message text from 'body' field
            text = ""
            if "body" in data:
                text = data["body"]
            
            if sender and text:
                messages.append((sender, text))
                print(f"✅ Message extracted - Sender: {sender}, Text: {text}")
            else:
                print(f"❌ Failed extraction - Sender: {sender}, Text: {text}")
                print(f"Available keys in payload: {list(data.keys())}")
                
        else:
            print(f"ℹ️ Ignoring event type: {payload.get('event')}")
                
    except Exception as e:
        print(f"❌ WAHA extraction error: {e}")
        print(f"Full payload: {payload}")
    
    return messages



def send_waha_reply(to_phone, message):
    """Enhanced WAHA send with connection retry and fallback"""
    if not WAHA_BASE_URL:
        print("❌ WAHA Base URL missing")
        return False
    
    # Clean and format phone number for Bangladesh
    clean_phone = re.sub(r'[^\d]', '', to_phone)
    
    # Add 880 country code if missing
    if not clean_phone.startswith('880'):
        clean_phone = '880' + clean_phone
    
    # WAHA format: phone@c.us
    chat_id = f"{clean_phone}@c.us"
    
    payload = {
        "session": WAHA_SESSION,
        "chatId": chat_id,
        "text": message
    }
    
    headers = {"Content-Type": "application/json"}
    
    # Retry mechanism with multiple attempts
    max_retries = 3
    retry_delay = [1, 2, 3]  # seconds
    
    for attempt in range(max_retries):
        try:
            print(f"📤 Attempt {attempt + 1}/{max_retries} - Sending to: {chat_id}")
            print(f"📝 Message: {message[:100]}...")
            print(f"🔗 URL: {WAHA_SEND_TEXT_URL}")
            
            response = requests.post(
                WAHA_SEND_TEXT_URL, 
                json=payload, 
                headers=headers, 
                timeout=30
            )
            
            print(f"📊 Response: {response.status_code}")
            print(f"📄 Body: {response.text}")
            
            success = response.status_code in [200, 201]
            
            if success:
                print("✅ WAHA message sent successfully")
                return True
            else:
                print(f"❌ Send failed: {response.status_code} - {response.text}")
                if attempt < max_retries - 1:
                    print(f"⏳ Retrying in {retry_delay[attempt]} seconds...")
                    import time
                    time.sleep(retry_delay[attempt])
                    continue
                
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection error on attempt {attempt + 1}: {e}")
            if "Connection refused" in str(e):
                print("🔍 WAHA server seems to be down or unreachable")
                print("💡 Solutions:")
                print("   1. Check if WAHA is running on the specified URL")
                print("   2. For localhost: Use ngrok to expose WAHA")
                print("   3. Update WAHA_BASE_URL environment variable")
                
            if attempt < max_retries - 1:
                print(f"⏳ Retrying in {retry_delay[attempt]} seconds...")
                import time
                time.sleep(retry_delay[attempt])
                continue
        except Exception as e:
            print(f"❌ Send exception on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                print(f"⏳ Retrying in {retry_delay[attempt]} seconds...")
                import time
                time.sleep(retry_delay[attempt])
                continue
    
    print("❌ All retry attempts failed")
    return False

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

@app.route("/webhook", methods=["GET", "POST"])
def webhook_handler():
    """Enhanced webhook handler with improved error handling"""
    if request.method == "GET":
        # WAHA webhook verification
        return jsonify({"status": "webhook_ready", "timestamp": datetime.now().isoformat()})
    
    try:
        payload = request.get_json()
        
        print("🔔" + "="*60)
        print("WAHA WEBHOOK RECEIVED")
        print(f"Headers: {dict(request.headers)}")
        print(f"Method: {request.method}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        print("="*60)
        
        messages = extract_waha_messages(payload)
        print(f"📨 Extracted {len(messages)} messages")
        
        for sender, text in messages:
            print(f"🔄 Processing: {sender} -> {text}")
            
            # Skip bot messages to prevent loops
            skip_phrases = ["sorry, our service", "মন্নিক্কবুম্", "dermijan.com", 
                           "temporarily unavailable", "technical issue", "connection"]
            if any(phrase.lower() in text.lower() for phrase in skip_phrases):
                print("⏭️ Skipping bot message")
                continue
            
            print("🤖 Getting AI response...")
            answer = get_perplexity_answer(text, sender)
            print(f"💬 AI Answer: {answer[:100]}...")
            
            print("📤 Sending reply...")
            success = send_waha_reply(sender, answer)
            print(f"✅ Send result: {success}")
            
            if not success:
                print("⚠️ Message send failed - check WAHA configuration")
        
        return jsonify({
            "status": "success", 
            "processed": len(messages),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/conversation/<user_id>", methods=["GET"])
def get_conversation(user_id):
    """Get conversation history"""
    history = mgr.get_history(user_id)
    return jsonify({"user_id": user_id, "conversation": history, "count": len(history)})

@app.route("/waha-status", methods=["GET"])
def check_waha_status():
    """Check WAHA server status with enhanced diagnostics"""
    try:
        # Check WAHA server health
        response = requests.get(f"{WAHA_BASE_URL}/api/sessions/{WAHA_SESSION}", timeout=10)
        if response.status_code == 200:
            session_data = response.json()
            return jsonify({
                "waha_status": "connected",
                "session_status": session_data.get("status"),
                "session_data": session_data,
                "base_url": WAHA_BASE_URL,
                "connection": "successful"
            })
        else:
            return jsonify({
                "waha_status": "error",
                "error_code": response.status_code,
                "error_message": response.text,
                "base_url": WAHA_BASE_URL,
                "connection": "failed"
            }), 500
    except requests.exceptions.ConnectionError as e:
        return jsonify({
            "waha_status": "connection_refused",
            "error": str(e),
            "base_url": WAHA_BASE_URL,
            "connection": "refused",
            "solutions": [
                "Check if WAHA is running on the specified URL",
                "For localhost: Use ngrok to expose WAHA publicly",
                "Update WAHA_BASE_URL environment variable to public URL",
                "Verify network connectivity"
            ]
        }), 500
    except Exception as e:
        return jsonify({
            "waha_status": "unknown_error",
            "error": str(e),
            "base_url": WAHA_BASE_URL,
            "connection": "unknown"
        }), 500

@app.route("/test-send", methods=["POST"])
def test_send_message():
    """Test WAHA message sending with diagnostics"""
    data = request.get_json()
    phone = data.get("phone")
    message = data.get("message", "Test message from Dermijan Bot")
    
    if not phone:
        return jsonify({"error": "Phone number required"}), 400
    
    print(f"🧪 Testing message send to {phone}")
    success = send_waha_reply(phone, message)
    
    return jsonify({
        "success": success,
        "phone": phone,
        "message": message,
        "waha_server": WAHA_BASE_URL,
        "session": WAHA_SESSION,
        "recommendation": "If failed, check WAHA_BASE_URL environment variable" if not success else "Message sent successfully"
    })

@app.route("/setup-waha-webhook", methods=["POST"])
def setup_waha_webhook():
    """Configure WAHA session with webhook and enhanced error handling"""
    data = request.get_json() or {}
    webhook_url = data.get("webhook_url", "https://webreplay-production.up.railway.app/webhook")
    
    session_config = {
        "name": WAHA_SESSION,
        "config": {
            "webhooks": [
                {
                    "url": webhook_url,
                    "events": ["message"],
                    "retries": {
                        "delaySeconds": 2,
                        "attempts": 3
                    }
                }
            ]
        }
    }
    
    try:
        response = requests.post(
            f"{WAHA_BASE_URL}/api/sessions/",
            json=session_config,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        return jsonify({
            "success": response.status_code in [200, 201],
            "status_code": response.status_code,
            "response": response.text,
            "webhook_configured": webhook_url,
            "waha_server": WAHA_BASE_URL
        })
    
    except requests.exceptions.ConnectionError as e:
        return jsonify({
            "error": "Cannot connect to WAHA server",
            "details": str(e),
            "waha_server": WAHA_BASE_URL,
            "solutions": [
                "Check if WAHA is running",
                "Verify WAHA_BASE_URL is correct",
                "Use ngrok if running localhost"
            ]
        }), 500
    except Exception as e:
        return jsonify({
            "error": str(e),
            "waha_server": WAHA_BASE_URL
        }), 500

@app.route("/", methods=["GET"])
def health_check():
    """Enhanced health check with configuration details"""
    try:
        redis_status = "connected" if redis_client.ping() else "disconnected"
    except:
        redis_status = "error"
    
    return jsonify({
        "status": "Dermijan Server Running - UX Optimized with DYNAMIC WAHA",
        "version": "Research-Based User Experience Enhanced - Enhanced WAHA Integration",
        "endpoints": ["/ask", "/webhook", "/conversation/<user_id>", "/waha-status", "/test-send", "/setup-waha-webhook"],
        "allowed_urls_count": len(ALLOWED_URLS),
        "redis_status": redis_status,
        "waha_config": {
            "base_url": WAHA_BASE_URL,
            "session": WAHA_SESSION,
            "send_endpoint": WAHA_SEND_TEXT_URL,
            "environment_controlled": True,
            "connection_retry": True
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
        },
        "setup_instructions": {
            "localhost": {
                "1": "Start WAHA: docker run -it --rm -p 3000:3000/tcp --name waha devlikeapro/waha",
                "2": "Use ngrok: ngrok http 3000",
                "3": "Set environment: WAHA_BASE_URL=https://your-ngrok-url.ngrok.io",
                "4": "Configure webhook: curl -X POST /setup-waha-webhook"
            },
            "production": {
                "1": "Deploy WAHA to public server",
                "2": "Set WAHA_BASE_URL environment variable",
                "3": "Configure webhook with public URL"
            }
        },
        "troubleshooting": {
            "connection_refused": "Use ngrok to expose localhost WAHA",
            "session_not_found": "Create WAHA session first",
            "webhook_failed": "Check webhook URL accessibility"
        }
    })

# ────────────────────────────────
# Main
# ────────────────────────────────
if __name__ == "__main__":
    print("🚀 Starting Dermijan Server - UX Research Enhanced with DYNAMIC WAHA")
    print(f"📋 Loaded {len(ALLOWED_URLS)} dermijan.com URLs")
    print("🎯 Features: Research-based formatting, Mobile-optimized, Visual hierarchy")
    print("✨ UX Enhancements: Short paragraphs, Strategic dots/hyphens, Scannable layout")
    print("📱 Mobile-first readability, Language-specific responses, Accessibility compliant")
    print(f"🔗 WAHA Integration: {WAHA_BASE_URL} (Session: {WAHA_SESSION})")
    print("⚙️ Environment Variables: WAHA_BASE_URL, WAHA_SESSION")
    print("💡 For localhost: Use ngrok to expose WAHA publicly")
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 8000)))
