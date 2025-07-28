from flask import Flask, request, jsonify
import requests
import json
import os
import redis
from datetime import datetime


app = Flask(__name__)


# API Configuration
PERPLEXITY_API_KEY = "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"
WASENDER_API_TOKEN = "37bf33ac1d6e4e6be8ae324373c2171400a1dd6183c6e501df646eb5f436ef6f"
WASENDER_SESSION = "TAKDIR"
WASENDER_API_URL = "https://wasenderapi.com/api/send-message"

# Redis Configuration
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# Dermijan.com Allowlist URLs
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


class ConversationManager:
    def __init__(self):
        self.redis_client = redis_client
        self.ttl_seconds = 604800  # 7 days (sliding window)
        self.max_messages = 20  # Keep last 20 messages per conversation
    
    def get_conversation_history(self, user_id: str) -> list:
        """Get conversation history for a user"""
        try:
            conversation_key = f"whatsapp_chat:{user_id}"
            messages = self.redis_client.lrange(conversation_key, 0, -1)
            
            # Parse and return messages (newest first, so reverse)
            conversation = []
            for msg in reversed(messages):
                try:
                    conversation.append(json.loads(msg))
                except:
                    continue
            
            print(f"📖 Retrieved {len(conversation)} messages for {user_id}")
            return conversation
            
        except Exception as e:
            print(f"❌ Error retrieving conversation for {user_id}: {e}")
            return []
    
    def store_message(self, user_id: str, message: str, sender: str = "user"):
        """Store message with sliding window TTL"""
        try:
            conversation_key = f"whatsapp_chat:{user_id}"
            
            message_data = {
                "message": message,
                "sender": sender,
                "timestamp": datetime.now().isoformat()
            }
            
            # Store message (newest messages at the beginning of list)
            self.redis_client.lpush(conversation_key, json.dumps(message_data))
            
            # Sliding expiration - extend TTL on each interaction
            self.redis_client.expire(conversation_key, self.ttl_seconds)
            
            # Keep only last N messages
            self.redis_client.ltrim(conversation_key, 0, self.max_messages - 1)
            
            print(f"💾 Stored message for {user_id} (sender: {sender})")
            
        except Exception as e:
            print(f"❌ Error storing message for {user_id}: {e}")
    
    def format_conversation_context(self, conversation_history: list) -> str:
        """Format conversation history for LLM context"""
        if not conversation_history:
            return ""
        
        context = "Previous conversation:\n"
        for msg in conversation_history[-10:]:  # Last 10 messages for context
            role = "User" if msg["sender"] == "user" else "Assistant"
            context += f"{role}: {msg['message']}\n"
        
        return context + "\nCurrent conversation:\n"


# Initialize conversation manager
conversation_manager = ConversationManager()


def get_perplexity_answer(question, user_id):
    """Get answer from Perplexity API with conversation context"""
    print(f"📥 Question received from {user_id}: {question}")
    
    # Get conversation history
    conversation_history = conversation_manager.get_conversation_history(user_id)
    conversation_context = conversation_manager.format_conversation_context(conversation_history)
    
    # Build restricted prompt with allowlist and context
    prompt = (
        f"Answer briefly using ONLY information from these dermijan.com pages:\n"
        + "\n".join(ALLOWED_URLS) + "\n\n"
        f"{conversation_context}"
        f"User: {question}\n\n"
        "Instructions: Give a SHORT, direct answer (4-6 lines maximum). "
        "Do NOT use outside information. Only use the provided dermijan.com URLs. "
        "If answer not found, reply: 'இந்த தகவல் எனது அங்கீকরிக্কப्পட்ட ஆதாரங்களில் கিডைক्कবিল्লை.' "
        "Do NOT include source URLs in your response. Keep it conversational and helpful."
    )
    
    url = "https://api.perplexity.ai/chat/completions"
    
    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": "You are a support assistant for a skin, hair, and body care clinic named *Dermijan*, interacting with customers on WhatsApp.\n\n**Guidelines:**\n\n- Use WhatsApp formatting:\n  - *Bold* for key terms (use asterisks)\n  - Bullets (with hyphens) for lists\n  - Keep replies short and user-friendly (4–6 lines per message)\n\n**Conversation Rules:**\n\n1. **Always address the user's specific query clearly.**\n2. **For any treatment or service question:**\n   - Check Dermijan's official knowledge base or service data before answering.\n   - If the info is unavailable, say:\n     \"That specific detail isn't available right now. Please contact our support team at *dermijanofficialcontact@gmail.com* or *+91 9003444435* for accurate information.\"\n3. **If the user asks for pricing:**\n   - If price is known:\n     \"*Price*: ₹XXXX (approximate, may vary based on consultation)\"\n   - If not available:\n     \"Sorry, this treatment's pricing isn't shared publicly. You can contact our team at *dermijanofficialcontact@gmail.com* or *+91 9003444435* to get the exact rates.\"\n4. **If the user mentions a skin, hair, or body issue (e.g., 'I have a skin issue'):**\n   - Ask follow-up questions to understand the concern:\n     \"I'm here to help! Could you please share more details about the skin issue you're facing? (e.g., since when, symptoms, affected area). This will help us suggest the right treatment.\"\n5. **General behavior:**\n   - Never repeat previous responses.\n   - Always offer the next step:\n     \"Would you like more info about this treatment?\" or \"Can I help you schedule a free consultation?\"\n   - Be polite, friendly, and empathetic—like a real person helping with care."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1200,
        "temperature": 0.1
    }
    
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print("📤 Sent to Perplexity, waiting...")
        
        if response.status_code == 200:
            reply = response.json()['choices'][0]['message']['content']
            print(f"✅ Perplexity Response: {reply[:100]}...")
            
            # Remove any source URLs that might slip through
            reply = remove_source_urls(reply)
            
            # Store user question and bot response
            conversation_manager.store_message(user_id, question, "user")
            conversation_manager.store_message(user_id, reply, "bot")
            
            if "இந்த தகவল்" in reply:
                return "இந্ত তকবল് এনদু অঙ্গীকরিক্কপ্পট্ট আদারঙ্গলিল् কিডাক্কবিল্লাই"
            
            return reply
        else:
            print(f"❌ Perplexity API error: {response.status_code} - {response.text}")
            return "மন্নিক্কবুম্, ইন্ত নেরত্তিল् সেবাই বজঙ্গ মুদিয়বিল্লাই।"
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return "মন্নিক্কবুम্, সিল সিক্কল্ এর্পট্টুল্লদু।"


def remove_source_urls(text):
    """Remove source URLs and references from response"""
    import re
    
    # Remove source sections
    text = re.sub(r'Sources?:.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'Reference:.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    
    # Remove URLs
    text = re.sub(r'https?://[^\s]+', '', text)
    text = re.sub(r'dermijan\.com[^\s]*', '', text)
    
    # Clean up extra whitespace
    text = re.sub(r'\n\s*\n', '\n', text)
    text = text.strip()
    
    return text


def extract_wasender_messages(payload):
    """Extract messages from WASender webhook payload"""
    messages = []
    try:
        # WASender format handling
        if "event" in payload and payload["event"] == "messages.upsert":
            if "data" in payload and "messages" in payload["data"]:
                message_data = payload["data"]["messages"]
                
                # Extract sender
                remote_jid = message_data.get("key", {}).get("remoteJid", "")
                sender = remote_jid.replace("@s.whatsapp.net", "").replace("+", "")
                
                # Extract message text
                message_content = message_data.get("message", {})
                text = ""
                if "conversation" in message_content:
                    text = message_content["conversation"]
                elif "extendedTextMessage" in message_content:
                    text = message_content["extendedTextMessage"].get("text", "")
                
                if sender and text:
                    messages.append((sender, text))
                    
    except Exception as e:
        print(f"❌ Message extraction error: {e}")
    
    return messages


def send_wasender_reply(to_phone, message):
    """Send reply via WASender API"""
    if not WASENDER_API_TOKEN:
        print("❌ WASender API token missing")
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
        if response.status_code in [200, 201]:
            print(f"✅ Message sent successfully to {to_phone}")
            return True
        else:
            print(f"❌ WASender API error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Send error: {str(e)}")
        return False


@app.route("/ask", methods=["POST"])
def ask_question():
    """Direct API endpoint for questions"""
    data = request.get_json()
    question = data.get("question")
    user_id = data.get("user_id", "anonymous")
    
    if not question:
        return jsonify({"reply": "কেল্বি কালিয়াক উল্লদু!"}), 400
    
    answer = get_perplexity_answer(question, user_id)
    return jsonify({"reply": answer})


@app.route("/webhook", methods=["POST"])
def webhook_handler():
    """WhatsApp webhook handler via WASender"""
    try:
        payload = request.get_json()
        print(f"📨 Incoming webhook: {json.dumps(payload, indent=2)}")
        
        # Extract message from WASender payload
        messages = extract_wasender_messages(payload)
        
        for sender, text in messages:
            print(f"📱 Message from {sender}: {text}")
            
            # Skip bot messages to prevent loops
            if any(phrase in text.lower() for phrase in ["sources:", "dermijan.com", "இந্ত তকবল্ এনদু"]):
                print("🔄 Bot message detected, skipping...")
                continue
            
            # Get answer from Perplexity with conversation context
            answer = get_perplexity_answer(text, sender)
            
            # Send reply via WASender
            send_wasender_reply(sender, answer)
        
        return jsonify({"status": "success"})
        
    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/conversation/<user_id>", methods=["GET"])
def get_conversation(user_id):
    """Get conversation history for a user (for debugging)"""
    history = conversation_manager.get_conversation_history(user_id)
    return jsonify({"user_id": user_id, "conversation": history, "count": len(history)})


@app.route("/", methods=["GET"])
def health_check():
    """Health check endpoint"""
    try:
        # Test Redis connection
        redis_status = "connected" if redis_client.ping() else "disconnected"
    except:
        redis_status = "error"
    
    return jsonify({
        "status": "MCP Dermijan Server Running",
        "endpoints": ["/ask", "/webhook", "/conversation/<user_id>"],
        "allowed_urls_count": len(ALLOWED_URLS),
        "redis_status": redis_status,
        "features": {
            "dermijan_allowlist": True,
            "perplexity_integration": True,
            "wasender_webhook": True,
            "conversation_persistence": True,
            "sliding_window_ttl": "7 days",
            "max_messages_per_user": 20
        }
    })


if __name__ == "__main__":
    print("🚀 Starting MCP Dermijan Server with Redis...")
    print(f"📋 Loaded {len(ALLOWED_URLS)} allowed dermijan.com URLs")
    print("🔗 Endpoints: /ask (direct), /webhook (WhatsApp), /conversation/<user_id> (debug)")
    print(f"💾 Redis TTL: 7 days (sliding window)")
    app.run(debug=True, host='0.0.0.0', port=8000)
