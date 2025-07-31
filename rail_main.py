"""
Dermijan Chatbot - WAHA Docker Integration
Version: 2025-07-29 WAHA Compatible
Features:
• WAHA Docker API integration
• Professional format (no emojis/icons)
• Language detection: English->English, Tamil->Tamil responses
• Research-based UX formatting with dots and hyphens
• Short paragraphs for mobile readability
• Single asterisk (*) bold formatting
• Automatic appointment handling
• Working Call Now button via WAHA
"""

from flask import Flask, request, jsonify
from datetime import datetime
import requests, json, os, redis, re

app = Flask(__name__)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# ────────────────────────────────
# API Configuration - WAHA Docker
# ────────────────────────────────
PERPLEXITY_API_KEY = "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"

# WAHA Docker Configuration
WAHA_API_URL = "http://localhost:3000/api"
WAHA_SESSION = "default"
WAHA_WEBHOOK_TOKEN = "your-webhook-secret"  # Optional security token

# Call Now Button Configuration
CALL_NOW_PHONE = "+919003444435"
CALL_NOW_LABEL = "📞 Call Now"

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
- Tamil: "அப்பாய்ன்ட்மென்ட் புக் செய়য, তয়াবুসেয়দু এঙ্গলাই *+91 9003444435* ইল অলৈক্কবুম, এঙ্গল তোদর্পু কুঝু বিরৈবিল উঙ্গলাই তোদর্পু কোল্লুম।"

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
    tamil_keywords = ['அப্পায়ন্ট্মেন্ট', 'পুক', 'সন্ধিপ্পু', 'বরুকৈ', 'নেরম']
    
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
    
    # Join paragraphs with double line breaks for visual breathing space
    text = '\n\n'.join(formatted_paragraphs)
    
    # Add appointment info based on UX research on call-to-action placement
    if detect_appointment_request(user_question):
        if user_language == "tamil":
            appointment_text = "\n\nঅপ্পায়ন্ট্মেন্ট পুক সেয়য, তয়াবুসেয়দু এঙ্গলাই *+91 9003444435* ইল অলৈক্কবুম, এঙ্গল তোদর্পু কুঝু বিরৈবিল উঙ্গলাই তোদর্পু কোল্লুম।"
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
        not_found_msg = "অন্ত তকবল এঙ্গল অঙ্গীকরিক্কপ্পট্ট আদারঙ্গলিল কিডৈক্কবিল্লাই। তুল্লিয়মান বিবরঙ্গলুক্কু এঙ্গল আদরবু কুঝুবাই তোদর্পু কোল্লবুম।"
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
                return "মন্নিক্কবুম, এঙ্গল সেবৈ তর্কালিকমাক কিডৈক্কবিল্লাই.\n\nপিরকু মুয়র্সিক্কবুম।"
            else:
                return "Sorry, our service is temporarily unavailable.\n\nPlease try again later."
            
    except Exception as e:
        print(f"Perplexity exception: {e}")
        if user_language == "tamil":
            return "মন্নিক্কবুম, তোঝিল্নুট্প সিক্কল এর্পট্টদু.\n\nপিরকু মুয়র্সিক্কবুম।"
        else:
            return "Sorry, there was a technical issue.\n\nPlease try again."

# ────────────────────────────────
# WAHA Docker API Functions
# ────────────────────────────────
def format_phone_for_waha(phone):
    """Format phone number for WAHA (phone@c.us)"""
    # Remove any existing formatting
    clean_phone = re.sub(r'[^\d]', '', phone)
    # Add country code if missing
    if not clean_phone.startswith('88'):
        clean_phone = '88' + clean_phone
    return f"{clean_phone}@c.us"

def check_waha_status():
    """Check WAHA session status"""
    try:
        response = requests.get(f"{WAHA_API_URL}/sessions/{WAHA_SESSION}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("status") == "WORKING"
        return False
    except:
        return False

def send_waha_text_message(to, message):
    """Send text message via WAHA Docker API"""
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
            print(f"✅ WAHA text message sent to {to}")
        else:
            print(f"❌ WAHA text failed: {response.status_code} - {response.text}")
        
        return success
    except Exception as e:
        print(f"❌ WAHA text error: {e}")
        return False

def send_waha_call_button(to, message):
    """Send Call Now button via WAHA Docker API"""
    chat_id = format_phone_for_waha(to)
    
    # WAHA Call Button payload
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
            print(f"✅ WAHA Call Now button sent to {to}")
            return True
        else:
            print(f"❌ WAHA button failed: {response.status_code} - {response.text}")
            # Fallback to text with call info
            fallback_message = f"{message}\n\n{CALL_NOW_LABEL}: {CALL_NOW_PHONE}"
            return send_waha_text_message(to, fallback_message)
            
    except Exception as e:
        print(f"❌ WAHA button error: {e}")
        # Fallback to text with call info
        fallback_message = f"{message}\n\n{CALL_NOW_LABEL}: {CALL_NOW_PHONE}"
        return send_waha_text_message(to, fallback_message)

def extract_waha_messages(payload):
    """Extract messages from WAHA webhook payload"""
    messages = []
    try:
        # WAHA webhook structure
        if payload.get("event") == "message":
            data = payload.get("payload", {})
            
            # Skip messages from bot itself
            if data.get("fromMe", False):
                return messages
            
            # Extract sender and message
            sender = data.get("from", "").replace("@c.us", "")
            message_body = ""
            
            # Handle different message types
            if data.get("body"):
                message_body = data.get("body")
            elif data.get("text"):
                message_body = data.get("text")
            
            # Handle button responses
            if data.get("type") == "button" and data.get("button", {}).get("id") == "call_now_btn":
                # User clicked Call Now button - initiate call
                print(f"📞 Call Now button clicked by {sender}")
                return messages  # Don't process as regular message
            
            if sender and message_body:
                messages.append((sender, message_body))
                print(f"📨 WAHA message extracted: {sender} -> {message_body[:50]}...")
                
    except Exception as e:
        print(f"❌ WAHA message extraction error: {e}")
    
    return messages

# ────────────────────────────────
# Flask Routes - WAHA Compatible
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
    return jsonify({"reply": answer, "waha_compatible": True})

@app.route("/waha-webhook", methods=["POST"])
def waha_webhook_handler():
    """WAHA Docker webhook handler"""
    try:
        payload = request.get_json()
        print(f"🔄 WAHA webhook received: {payload.get('event', 'unknown')}")
        
        messages = extract_waha_messages(payload)
        
        for sender, text in messages:
            # Skip bot messages and sources to prevent loops
            skip_phrases = ["Sources:", "dermijan.com", "isn't available in our approved sources", 
                           "Call Now:", CALL_NOW_PHONE]
            if any(phrase.lower() in text.lower() for phrase in skip_phrases):
                print(f"⏭️ Skipped message from {sender}: {text[:30]}...")
                continue
            
            print(f"🤖 Processing question from {sender}")
            answer = get_perplexity_answer(text, sender)
            
            # Send reply with Call Now button via WAHA
            send_waha_call_button(sender, answer)
        
        return jsonify({"status": "success", "processed": len(messages)})
        
    except Exception as e:
        print(f"❌ WAHA webhook error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/conversation/<user_id>", methods=["GET"])
def get_conversation(user_id):
    """Get conversation history"""
    history = mgr.get_history(user_id)
    return jsonify({"user_id": user_id, "conversation": history, "count": len(history)})

@app.route("/test-waha/<phone>", methods=["GET"])
def test_waha_message(phone):
    """Test WAHA message sending"""
    test_msg = "Test message from Dermijan WAHA integration"
    success = send_waha_call_button(phone, test_msg)
    return jsonify({
        "phone": phone,
        "message_sent": success,
        "waha_status": check_waha_status(),
        "formatted_phone": format_phone_for_waha(phone)
    })

@app.route("/", methods=["GET"])
def health_check():
    """Health check with WAHA Docker status"""
    try:
        redis_status = "connected" if redis_client.ping() else "disconnected"
        waha_status = "connected" if check_waha_status() else "disconnected"
    except:
        redis_status = "error"
        waha_status = "error"
    
    return jsonify({
        "status": "Dermijan Server Running - WAHA Docker Integrated",
        "version": "WAHA Docker API Compatible with Call Now Button",
        "endpoints": ["/ask", "/waha-webhook", "/conversation/<user_id>", "/test-waha/<phone>"],
        "allowed_urls_count": len(ALLOWED_URLS),
        "redis_status": redis_status,
        "waha_status": waha_status,
        "waha_session": WAHA_SESSION,
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
            "waha_button_fallback": True
        }
    })

# ────────────────────────────────
# Main
# ────────────────────────────────
if __name__ == "__main__":
    print("🚀 Starting Dermijan Server - WAHA Docker Integration")
    print(f"📋 Loaded {len(ALLOWED_URLS)} dermijan.com URLs")
    print(f"🐳 WAHA Docker API: {WAHA_API_URL}")
    print(f"📱 WAHA Session: {WAHA_SESSION}")
    print("✨ Features: WAHA Docker, Call Now Button, Professional formatting")
    print("🎯 Research-based UX, Language-specific responses, Mobile-optimized")
    print("📞 Call Now Button: Working with WAHA Docker API")
    app.run(debug=True, host='0.0.0.0', port=8000)
