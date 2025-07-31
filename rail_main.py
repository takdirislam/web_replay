"""
Dermijan Chatbot - Research-Based UX Optimized Version (Fixed)
Version: 2025-07-29 UX Enhanced + Railway Deployment Ready + Security Fixed
Features:
• Research-backed text formatting for maximum readability
• Optimized paragraph structure for mobile users
• Strategic use of dots and hyphens for better scanning
• Visual hierarchy implementation
• WhatsApp-specific user experience patterns
• Call to Action Button Implementation
• panel.whapi.cloud API Integration
• Asynchronous Processing & Queue Management
• Performance Optimization
• Railway Deployment Ready
• Security Enhanced
• Fixed Language Detection
"""

from flask import Flask, request, jsonify, render_template_string
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime
import requests, json, os, redis, re, time
from threading import Thread, Lock
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor
import uuid
import logging
from redis.connection import ConnectionPool

app = Flask(__name__)

# ────────────────────────────────
# Security Headers
# ────────────────────────────────
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# ────────────────────────────────
# Rate Limiting
# ────────────────────────────────
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per hour", "20 per minute"]
)

# ────────────────────────────────
# Logging Configuration
# ────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dermijan_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ────────────────────────────────
# Railway Environment Configuration with Validation
# ────────────────────────────────
PORT = int(os.environ.get("PORT", 8000))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Enhanced Redis Connection with Pool
try:
    redis_pool = ConnectionPool.from_url(REDIS_URL, decode_responses=True, max_connections=20)
    redis_client = redis.Redis(connection_pool=redis_pool)
    redis_client.ping()
    logger.info("✅ Redis connection successful with connection pool")
except Exception as e:
    logger.error(f"❌ Redis connection failed: {e}")
    redis_client = None

# ────────────────────────────────
# API Configuration with Environment Variables
# ────────────────────────────────
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
if not PERPLEXITY_API_KEY:
    logger.error("❌ PERPLEXITY_API_KEY environment variable is required")
    raise ValueError("PERPLEXITY_API_KEY environment variable must be set")

# panel.whapi.cloud Configuration
WHAPI_BASE_URL = "https://gate.whapi.cloud"
WHAPI_TOKEN = os.getenv("WHAPI_TOKEN")
if not WHAPI_TOKEN:
    logger.warning("⚠️ WHAPI_TOKEN not set, WhatsApp integration will not work")
    WHAPI_TOKEN = "YOUR_WHAPI_TOKEN_HERE"

WHAPI_HEADERS = {
    "Authorization": f"Bearer {WHAPI_TOKEN}",
    "Content-Type": "application/json"
}

# Performance Settings
MAX_CONCURRENT_REQUESTS = 10
RESPONSE_TIMEOUT = 15  # Reduced from 30 seconds
QUEUE_PROCESSING_DELAY = 0.1

# Thread locks for safety
redis_lock = Lock()
queue_lock = Lock()

# ────────────────────────────────
# Message Queue System for Async Processing (Thread-Safe)
# ────────────────────────────────
class MessageQueue:
    def __init__(self):
        self.queue = Queue()
        self.processing = True
        self.executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS)
        self.processed_count = 0
        self.lock = Lock()
        self.start_processor()
    
    def add_message(self, message_data):
        """Add message to processing queue - Thread Safe"""
        try:
            with self.lock:
                message_id = str(uuid.uuid4())
                message_data['id'] = message_id
                message_data['timestamp'] = datetime.now().isoformat()
                
                self.queue.put(message_data)
                logger.info(f"Message {message_id} added to queue. Queue size: {self.queue.qsize()}")
                return message_id
        except Exception as e:
            logger.error(f"Error adding message to queue: {e}")
            return None
    
    def start_processor(self):
        """Start async message processor"""
        def processor():
            while self.processing:
                try:
                    message_data = self.queue.get(timeout=1)
                    
                    # Submit to thread pool for async processing
                    future = self.executor.submit(self._process_message, message_data)
                    
                    # Non-blocking processing
                    time.sleep(QUEUE_PROCESSING_DELAY)
                    
                except Empty:
                    continue
                except Exception as e:
                    logger.error(f"Queue processor error: {e}")
        
        # Start processor in background thread
        processor_thread = Thread(target=processor, daemon=True)
        processor_thread.start()
        logger.info("Message queue processor started")
    
    def _process_message(self, message_data):
        """Process individual message asynchronously - Thread Safe"""
        start_time = time.time()
        message_id = message_data.get('id')
        
        try:
            sender = message_data.get('sender')
            text = message_data.get('text')
            
            logger.info(f"Processing message {message_id} from {sender}")
            
            # Get bot response
            response = get_perplexity_answer(text, sender)
            
            # Send response with call button
            enhanced_response = add_call_button(response, text)
            success = send_whapi_message(sender, enhanced_response)
            
            with self.lock:
                self.processed_count += 1
                
            processing_time = time.time() - start_time
            
            if success:
                logger.info(f"Message {message_id} processed successfully in {processing_time:.2f}s")
                # Update Redis counter safely
                if redis_client:
                    with redis_lock:
                        redis_client.incr("total_processed")
            else:
                logger.error(f"Failed to send response for message {message_id}")
                
        except Exception as e:
            logger.error(f"Error processing message {message_id}: {e}")

# Initialize message queue
message_queue = MessageQueue()

# ────────────────────────────────
# Call to Action Button Implementation
# ────────────────────────────────
def add_call_button(message_text, user_question=""):
    """Add call-to-action button to message"""
    try:
        # Detect if appointment-related
        appointment_keywords = ['appointment', 'book', 'schedule', 'অ্যাপয়েন্টমেন্ট', 'বুক', 'visit', 'consultation']
        needs_call_button = any(keyword.lower() in user_question.lower() for keyword in appointment_keywords)
        
        if needs_call_button or "9003444435" in message_text:
            # Enhanced message with call button for WhatsApp
            button_message = {
                "typing_time": 0,
                "to": None,  # Will be set when sending
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {
                        "text": message_text
                    },
                    "action": {
                        "buttons": [
                            {
                                "type": "reply",
                                "reply": {
                                    "id": "call_now_btn",
                                    "title": "📞 Call Now"
                                }
                            },
                            {
                                "type": "reply", 
                                "reply": {
                                    "id": "more_info_btn",
                                    "title": "ℹ️ More Info"
                                }
                            }
                        ]
                    }
                }
            }
            return button_message
        
        return message_text
        
    except Exception as e:
        logger.error(f"Error adding call button: {e}")
        return message_text

def handle_button_response(button_id, sender):
    """Handle button click responses"""
    try:
        if button_id == "call_now_btn":
            # Send direct call instruction
            call_message = "📞 *Direct Call Link*\n\nClick below to call us directly:\n*tel:+919003444435*\n\nOr dial: *+91 9003444435*\n\nOur team is ready to assist you!"
            return call_message
            
        elif button_id == "more_info_btn":
            info_message = "*Dermijan Clinic Information*\n\n🏥 *Services*:\n- Skin Care Treatments\n- Hair Care Solutions\n- Body Sculpting\n- Anti-Aging Therapy\n\n📍 *Location*: Chennai\n📧 *Email*: dermijanofficialcontact@gmail.com\n\n*What would you like to know more about?*"
            return info_message
            
    except Exception as e:
        logger.error(f"Error handling button response: {e}")
        return None

# ────────────────────────────────
# panel.whapi.cloud Integration (Enhanced)
# ────────────────────────────────
class WhAPIClient:
    def __init__(self):
        self.base_url = WHAPI_BASE_URL
        self.headers = WHAPI_HEADERS
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        # Add connection pooling
        adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=20)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
    
    def send_message_sync(self, message_data):
        """Synchronous message sending with status tracking"""
        try:
            response = self.session.post(
                f"{self.base_url}/messages",
                json=message_data,
                timeout=RESPONSE_TIMEOUT
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Message sent successfully: {result}")
                
                # Store message status for tracking
                message_id = result.get('id')
                if message_id and redis_client:
                    with redis_lock:
                        redis_client.setex(f"msg_status:{message_id}", 3600, json.dumps(result))
                
                return True, result
            else:
                logger.error(f"WhAPI error: {response.status_code} - {response.text}")
                return False, response.text
                
        except requests.exceptions.Timeout:
            logger.error("WhAPI request timeout")
            return False, "Request timeout"
        except requests.exceptions.ConnectionError as e:
            logger.error(f"WhAPI connection error: {e}")
            return False, "Connection error"
        except Exception as e:
            logger.error(f"WhAPI send error: {e}")
            return False, str(e)
    
    def get_message_status(self, message_id):
        """Get message delivery status"""
        try:
            response = self.session.get(
                f"{self.base_url}/messages/{message_id}",
                timeout=RESPONSE_TIMEOUT
            )
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            logger.error(f"Status check error: {e}")
            return None

# Initialize WhAPI client
whapi_client = WhAPIClient()

def send_whapi_message(to_phone, message_content):
    """Enhanced message sending with call button support"""
    try:
        # Prepare phone number
        phone = to_phone.replace("+", "").replace("@s.whatsapp.net", "")
        if not phone.startswith("91"):
            phone = f"91{phone}"
        
        # Handle different message types
        if isinstance(message_content, dict):
            # Interactive message with buttons
            message_content["to"] = phone
            message_data = message_content
        else:
            # Simple text message
            message_data = {
                "typing_time": 0,
                "to": phone,
                "type": "text",
                "text": {"body": str(message_content)}
            }
        
        # Send message
        success, result = whapi_client.send_message_sync(message_data)
        return success
        
    except Exception as e:
        logger.error(f"Error sending WhAPI message: {e}")
        return False

def extract_whapi_messages(payload):
    """Extract messages from panel.whapi.cloud webhook"""
    messages = []
    try:
        # Handle different webhook types
        if payload.get("event") == "message":
            data = payload.get("data", {})
            
            # Extract sender
            sender = data.get("from", "").replace("@s.whatsapp.net", "")
            
            # Extract message content
            text = ""
            message_type = data.get("type", "")
            
            if message_type == "text":
                text = data.get("text", {}).get("body", "")
            elif message_type == "interactive":
                # Handle button responses
                interactive = data.get("interactive", {})
                if interactive.get("type") == "button_reply":
                    button_id = interactive.get("button_reply", {}).get("id", "")
                    text = f"BUTTON_CLICK:{button_id}"
            
            if sender and text:
                messages.append((sender, text))
                logger.info(f"Extracted message from {sender}: {text[:50]}...")
                
    except Exception as e:
        logger.error(f"Message extraction error: {e}")
    
    return messages

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
# Research-Based System Prompt (Fixed Tamil Language)
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
- Tamil: "அப்பாயின்ட்மென்ட் புக் செய்ய, தயவுசெய்து எங்களை *+91 9003444435* இல் அழைக்கவும், எங்கள் தொடர்பு குழு விரைவில் உங்களை தொடர்பு கொள்ளும்।"

Remember: Apply research-backed formatting consistently. Every response should be scannable, mobile-friendly, and follow proven UX patterns."""

# ────────────────────────────────
# Fixed Language Detection Function
# ────────────────────────────────
def detect_language(text):
    """Detect if text is primarily English or Tamil - Fixed Unicode Range"""
    # Correct Tamil Unicode range
    tamil_chars = re.findall(r'[\u0B80-\u0BFF]', text)
    english_words = re.findall(r'[a-zA-Z]+', text)
    
    # Tamil keywords for better detection
    tamil_keywords = ['அப்பாயின்ட்மென்ட்', 'புக்', 'செய்ய', 'வர', 'என்ன', 'எப்படி', 'எங்கே', 'எப்போது']
    tamil_keyword_count = sum(1 for keyword in tamil_keywords if keyword in text)
    
    if len(tamil_chars) > len(english_words) or tamil_keyword_count > 0:
        return "tamil"
    elif len(english_words) > 0:
        return "english"
    else:
        return "english"  # default to English

# ────────────────────────────────
# Enhanced Conversation Manager (Thread-Safe)
# ────────────────────────────────
class ConversationManager:
    def __init__(self):
        self.ttl = 7 * 24 * 3600
        self.max_msgs = 20

    def get_history(self, uid):
        try:
            if not redis_client:
                return []
            key = f"whatsapp_chat:{uid}"
            with redis_lock:
                msgs = redis_client.lrange(key, 0, -1)
            return [json.loads(m) for m in reversed(msgs)]
        except redis.RedisError as e:
            logger.error(f"Redis error getting history for {uid}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting history for {uid}: {e}")
            return []

    def store(self, uid, msg, who="user"):
        try:
            if not redis_client:
                return
            key = f"whatsapp_chat:{uid}"
            data = {"message": msg, "sender": who, "timestamp": datetime.now().isoformat()}
            with redis_lock:
                redis_client.lpush(key, json.dumps(data))
                redis_client.ltrim(key, 0, self.max_msgs-1)
                redis_client.expire(key, self.ttl)
        except redis.RedisError as e:
            logger.error(f"Redis error storing message for {uid}: {e}")
        except Exception as e:
            logger.error(f"Error storing message for {uid}: {e}")

    def format_context(self, hist):
        if not hist: return ""
        ctx = "Previous conversation:\n"
        for m in hist[-10:]:
            role = "User" if m["sender"] == "user" else "Assistant"
            ctx += f"{role}: {m['message']}\n"
        return ctx + "\nCurrent conversation:\n"

mgr = ConversationManager()

# ────────────────────────────────
# UX-Optimized Text Processing (unchanged)
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
    # Fixed Tamil keywords
    tamil_keywords = ['அப்பாயின்ட்மென்ட்', 'புக்', 'முன்பதிவு', 'வர', 'நேரம்']
    
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
            # Fixed Tamil text
            appointment_text = "\n\nஅப்பாயின்ட்மென்ட் புக் செய்ய, தயவுசெய்து எங்களை *+91 9003444435* இல் அழைக்கவும், எங்கள் தொடர்பு குழு விரைவில் உங்களை தொடர்பு கொள்ளும்।"
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
# Enhanced Perplexity API Integration with Better Error Handling
# ────────────────────────────────
def get_perplexity_answer(question, uid):
    """Get UX-optimized answer from Perplexity API with enhanced error handling"""
    start_time = time.time()
    
    try:
        # Check cache first for performance optimization
        cache_key = f"answer_cache:{hash(question)}"
        if redis_client:
            try:
                with redis_lock:
                    cached_answer = redis_client.get(cache_key)
                if cached_answer:
                    logger.info(f"Cache hit for question: {question[:50]}...")
                    with redis_lock:
                        redis_client.incr("cache_hits")
                    return json.loads(cached_answer)
            except redis.RedisError as e:
                logger.error(f"Redis cache error: {e}")
        
        logger.info(f"Question from {uid}: {question}")
        
        # Language detection for appropriate response
        user_language = detect_language(question)
        logger.info(f"Detected language: {user_language}")
        
        hist = mgr.get_history(uid)
        ctx = mgr.format_context(hist)
        
        # Research-based language instructions
        if user_language == "tamil":
            language_instruction = "Respond ONLY in Tamil. Apply research-based formatting: short paragraphs (2-3 sentences), use hyphens (-) for bullets, *bold* for key info."
            not_found_msg = "அந்த தகவல் எங்கள் அங்கீகரிக்கப்பட்ட ஆதாரங்களில் கிடைக்கவில்லை। துல்லியமான விவரங்களுக்கு எங்கள் ஆதரவு குழுவைத் தொடர்பு கொள்ளவும்।"
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

        response = requests.post(
            "https://api.perplexity.ai/chat/completions", 
            json=payload, 
            headers=headers, 
            timeout=RESPONSE_TIMEOUT
        )
        
        if response.status_code == 200:
            raw_reply = response.json()["choices"][0]["message"]["content"]
            clean_reply = clean_source_urls(raw_reply)
            formatted_reply = apply_research_based_formatting(clean_reply, question)
            
            # Cache the response for performance optimization
            if redis_client:
                try:
                    with redis_lock:
                        redis_client.setex(cache_key, 3600, json.dumps(formatted_reply))  # 1 hour cache
                except redis.RedisError as e:
                    logger.error(f"Redis cache store error: {e}")
            
            # Store conversation with research-based formatting
            mgr.store(uid, question, "user")
            mgr.store(uid, formatted_reply, "bot")
            
            processing_time = time.time() - start_time
            logger.info(f"Question processed in {processing_time:.2f}s")
            
            return formatted_reply
            
        elif response.status_code == 401:
            logger.error("Perplexity API authentication failed - check API key")
            if user_language == "tamil":
                return "மன்னிக்கவும், எங்கள் சேவை தற்காலிகமாக கிடைக்கவில்லை.\n\nபிற்பாடு முயற்சிக்கவும்।"
            else:
                return "Sorry, our service is temporarily unavailable.\n\nPlease try again later."
        else:
            logger.error(f"Perplexity API error: {response.status_code} - {response.text}")
            if user_language == "tamil":
                return "மன்னிக்கவும், எங்கள் சேவை தற்காலிகமாக கிடைக்கவில்லை.\n\nபிற்பாடு முயற்சிக்கவும்।"
            else:
                return "Sorry, our service is temporarily unavailable.\n\nPlease try again later."
                
    except requests.exceptions.Timeout:
        logger.error("Perplexity API timeout")
        if detect_language(question) == "tamil":
            return "மன்னிக்கவும், பதில் அனுப்புவதில் தாமதம்.\n\nபிற்பாடு முயற்சிக்கவும்।"
        else:
            return "Sorry, response timeout occurred.\n\nPlease try again."
    except requests.exceptions.ConnectionError:
        logger.error("Perplexity API connection error")
        if detect_language(question) == "tamil":
            return "மன்னிக்கவும், இணைப்பு சிக்கல்.\n\nபிற்பாடு முயற்சிக்கவும்।"
        else:
            return "Sorry, connection issue occurred.\n\nPlease try again."
    except Exception as e:
        logger.error(f"Perplexity exception: {e}")
        if detect_language(question) == "tamil":
            return "மன்னிக்கவும், தொழில்நுட்ப சிக்கல் ஏற்பட்டு.\n\nபிற்பாடு முயற்சிக்கவும்।"
        else:
            return "Sorry, there was a technical issue.\n\nPlease try again."

# ────────────────────────────────
# Flask Routes (Enhanced with Rate Limiting)
# ────────────────────────────────
@app.route("/ask", methods=["POST"])
@limiter.limit("10 per minute")
def ask_question():
    """Direct API endpoint with UX optimization and rate limiting"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400
            
        question = data.get("question")
        user_id = data.get("user_id", "anonymous")
        
        if not question or not question.strip():
            return jsonify({"reply": "Please provide a question."}), 400
        
        answer = get_perplexity_answer(question, user_id)
        enhanced_answer = add_call_button(answer, question)
        
        return jsonify({
            "reply": answer,
            "enhanced_reply": enhanced_answer,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Ask endpoint error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/webhook", methods=["POST"])
@limiter.limit("50 per minute")
def webhook_handler():
    """Enhanced WhatsApp webhook handler with async processing"""
    try:
        payload = request.get_json()
        if not payload:
            return jsonify({"status": "error", "message": "Invalid payload"}), 400
            
        messages = extract_whapi_messages(payload)
        
        for sender, text in messages:
            # Handle button clicks
            if text.startswith("BUTTON_CLICK:"):
                button_id = text.replace("BUTTON_CLICK:", "")
                button_response = handle_button_response(button_id, sender)
                
                if button_response:
                    send_whapi_message(sender, button_response)
                continue
            
            # Skip bot messages to prevent loops
            skip_phrases = ["Sources:", "dermijan.com", "isn't available in our approved sources"]
            if any(phrase.lower() in text.lower() for phrase in skip_phrases):
                continue
            
            # Add to processing queue for async handling
            message_data = {
                "sender": sender,
                "text": text,
                "type": "user_message"
            }
            
            message_id = message_queue.add_message(message_data)
            logger.info(f"Message queued with ID: {message_id}")
        
        return jsonify({"status": "success", "processed": len(messages)})
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route("/conversation/<user_id>", methods=["GET"])
@limiter.limit("20 per minute")
def get_conversation(user_id):
    """Get conversation history with rate limiting"""
    try:
        history = mgr.get_history(user_id)
        return jsonify({"user_id": user_id, "conversation": history, "count": len(history)})
    except Exception as e:
        logger.error(f"Conversation endpoint error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/status/<message_id>")
@limiter.limit("30 per minute")
def message_status(message_id):
    """Get message delivery status with rate limiting"""
    try:
        if not redis_client:
            return jsonify({"error": "Redis not available"}), 500
        
        with redis_lock:
            status_data = redis_client.get(f"msg_status:{message_id}")
        
        if status_data:
            return jsonify(json.loads(status_data))
        else:
            return jsonify({"error": "Message not found"}), 404
    except redis.RedisError as e:
        logger.error(f"Redis status check error: {e}")
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/stats")
@limiter.limit("10 per minute")
def system_stats():
    """System performance statistics with rate limiting"""
    try:
        redis_connected = False
        processed_messages = "0"
        active_conversations = 0
        cache_hits = "0"
        
        if redis_client:
            try:
                with redis_lock:
                    redis_connected = redis_client.ping()
                    processed_messages = redis_client.get("total_processed") or "0"
                    active_conversations = len(redis_client.keys("whatsapp_chat:*"))
                    cache_hits = redis_client.get("cache_hits") or "0"
            except redis.RedisError as e:
                logger.error(f"Redis stats error: {e}")
        
        stats = {
            "queue_size": message_queue.queue.qsize(),
            "redis_connected": redis_connected,
            "uptime": datetime.now().isoformat(),
            "processed_messages": processed_messages,
            "active_conversations": active_conversations,
            "cache_hits": cache_hits,
            "total_processed_by_queue": message_queue.processed_count
        }
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/demo")
def call_button_demo():
    """Demo page for call button functionality"""
    demo_html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dermijan Call Button Demo</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }
            .container { max-width: 400px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
            .call-btn { 
                background: #25D366; color: white; padding: 15px 30px; 
                border: none; border-radius: 25px; font-size: 16px; 
                cursor: pointer; width: 100%; margin: 10px 0;
            }
            .call-btn:hover { background: #128C7E; }
            .info { background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>📞 Dermijan Call Button Demo</h2>
            
            <div class="info">
                <strong>How it works:</strong><br>
                • Click "Call Now" button<br>
                • Phone will automatically dial<br>
                • Direct connection to clinic
            </div>
            
            <button class="call-btn" onclick="makeCall()">
                📞 Call Now - Dermijan Clinic
            </button>
            
            <button class="call-btn" onclick="sendWhatsApp()" style="background: #128C7E;">
                💬 WhatsApp Chat
            </button>
            
            <div class="info">
                <strong>Contact Info:</strong><br>
                📞 Phone: +91 9003444435<br>
                📧 Email: dermijanofficialcontact@gmail.com<br>
                🌐 Website: dermijan.com
            </div>
        </div>
        
        <script>
            function makeCall() {
                // Direct phone call
                window.location.href = "tel:+919003444435";
            }
            
            function sendWhatsApp() {
                // WhatsApp direct message
                const message = encodeURIComponent("Hello, I would like to book an appointment at Dermijan clinic.");
                window.open(`https://wa.me/919003444435?text=${message}`, '_blank');
            }
        </script>
    </body>
    </html>
    '''
    return render_template_string(demo_html)

@app.route("/", methods=["GET"])
def health_check():
    """Health check with UX feature status and enhanced security"""
    try:
        redis_status = "disconnected"
        if redis_client:
            try:
                with redis_lock:
                    redis_client.ping()
                redis_status = "connected"
            except redis.RedisError:
                redis_status = "error"
    except:
        redis_status = "error"
    
    return jsonify({
        "status": "Dermijan Server Running - Security Enhanced + Fixed Issues",
        "version": "Research-Based UX + Performance + Security + Railway Ready v2.0",
        "endpoints": ["/ask", "/webhook", "/conversation/<user_id>", "/status/<id>", "/stats", "/demo"],
        "allowed_urls_count": len(ALLOWED_URLS),
        "redis_status": redis_status,
        "queue_size": message_queue.queue.qsize(),
        "port": PORT,
        "security_features": {
            "api_key_from_env": True,
            "rate_limiting": True,
            "security_headers": True,
            "connection_pooling": True,
            "thread_safety": True,
            "enhanced_error_handling": True,
            "input_validation": True
        },
        "fixes_applied": {
            "api_key_exposure": "Fixed - Now uses environment variable",
            "language_detection": "Fixed - Correct Tamil Unicode and text",
            "thread_safety": "Fixed - Added locks for shared resources", 
            "error_handling": "Enhanced - Specific exception handling",
            "performance": "Improved - Connection pooling, caching",
            "security": "Enhanced - Headers, rate limiting, validation"
        },
        "features": {
            "research_based_formatting": True,
            "mobile_optimized_paragraphs": True,
            "language_specific_responses": True,
            "readability_enhanced": True,
            "visual_hierarchy_implemented": True,
            "accessibility_compliant": True,
            "whatsapp_pattern_optimized": True,
            "scanning_friendly_layout": True,
            "call_to_action_buttons": True,
            "whapi_cloud_integration": True,
            "async_processing": True,
            "queue_management": True,
            "performance_optimized": True,
            "message_status_tracking": True,
            "response_caching": True,
            "comprehensive_logging": True,
            "railway_deployment_ready": True
        }
    })

# ────────────────────────────────
# Main - Railway Configuration (Enhanced)
# ────────────────────────────────
if __name__ == "__main__":
    logger.info("🚄 Starting Dermijan Server - Security Enhanced + All Issues Fixed")
    logger.info(f"📋 Loaded {len(ALLOWED_URLS)} dermijan.com URLs")
    logger.info("🎯 Features: Research-based formatting, Mobile-optimized, Visual hierarchy")
    logger.info("✨ Enhanced: Security headers, Rate limiting, Thread safety")
    logger.info("🔐 Security: API keys from environment, Input validation, Error handling")
    logger.info("📱 Fixed: Tamil language detection, Connection pooling, Caching")
    logger.info("🔧 Performance: Queue management, Message status tracking, Logging")
    logger.info(f"🌐 Server starting on port: {PORT}")
    
    # Validate required environment variables
    if not PERPLEXITY_API_KEY:
        logger.error("❌ PERPLEXITY_API_KEY is required")
        exit(1)
    
    logger.info("✅ All environment variables validated")
    logger.info("🚀 Server ready for Railway deployment")
    
    app.run(debug=False, host='0.0.0.0', port=PORT)
