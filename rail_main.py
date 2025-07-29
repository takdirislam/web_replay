from flask import Flask, request, jsonify
import requests
import json
import os
import redis
from datetime import datetime

# ==================== Config =======================
app = Flask(__name__)
PERPLEXITY_API_KEY   = os.environ.get('PERPLEXITY_API_KEY')
WASENDER_API_TOKEN   = os.environ.get('WASENDER_API_TOKEN')
WASENDER_SESSION     = os.environ.get('WASENDER_SESSION', 'TAKDIR')
WASENDER_API_URL     = "https://wasenderapi.com/api/send-message"
REDIS_URL            = os.environ.get('REDIS_URL', 'redis://localhost:6379')
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# ================== Allowlist =======================
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

# ============= Visual Reply Template Logic =============
DIV   = "────────────────────"
EMJ   = {"skin": "✨", "hair": "💇‍♀️", "body": "💪"}

def hdr(txt, icon="✨"):
    return f"*{icon} {txt}*\n"

FOOTER = f"""{DIV}
📞 *Call*: +91 9003444435  |  ✉️ *Email*: dermijanofficialcontact@gmail.com
👍 *Reply* “YES” to book a free consultation!"""

def tpl_welcome(name="there"):
    return [
        hdr("Welcome to Dermijan!", "🌟") +
        f"Hi {name} 👋, I’m your assistant for *skin, hair & body* care.\n" + FOOTER,
        hdr("How can we help today?", "❓") +
        "- I have a *skin* concern\n- Worried about *hair* fall\n- Need *body* shaping tips\n👉 Tap a line or type your concern.",
        hdr("Quick questions for you", "📝") +
        "1️⃣ When did the issue start?\n2️⃣ Symptoms & area?\n3️⃣ Any prior treatment?\n(Short answers are fine!)"
    ]

def tpl_reco(tag):
    icon = EMJ.get(tag, "✨")
    title, benefits = "", ""
    if tag == "skin":
        title    = "Skin Glow & Rejuvenation"
        benefits = "✅ Brighter complexion\n✅ Proven tech\n✅ Minimal downtime"
    elif tag == "hair":
        title    = "Advanced Hair Regrowth"
        benefits = "✅ Visible regrowth\n✅ Strengthens roots\n✅ Non-surgical"
    elif tag == "body":
        title    = "Body Sculpt & Tone"
        benefits = "✅ Inch-loss\n✅ Targets stubborn fat\n✅ Quick, painless"
    else:
        title    = "Dermijan Treatments"
        benefits = "✨ Expert skin, hair & body care"

    return (
        hdr(title, icon) +
        benefits +
        f"\n{DIV}\nReady to begin? Reply *BOOK* and we'll schedule a free consult. 😊\n" +
        FOOTER
    )

def tpl_followup():
    return (
        hdr("A few more details", "🧐") +
        "- Issue duration?\n- Area & symptoms?\n- Treatments tried?\n👉 Share to get best advice."
    )

def tpl_book():
    return (f"🎉 *Great!* Please call *+91 9003444435* or email *dermijanofficialcontact@gmail.com* "
            "to confirm your slot.\nWe look forward to helping you!")

# ========== Conversation Manager (Redis) ==============
class ConversationManager:
    def __init__(self):
        self.redis_client = redis_client
        self.ttl_seconds = 7 * 24 * 3600  # 7 days
        self.max_messages = 20

    def get_conversation_history(self, user_id: str) -> list:
        try:
            k = f"whatsapp_chat:{user_id}"
            msgs = self.redis_client.lrange(k, 0, -1)
            return [json.loads(x) for x in reversed(msgs)]
        except Exception as e:
            print(f"❌ Error retrieving history: {e}")
            return []

    def store_message(self, user_id: str, message: str, sender: str = "user"):
        try:
            k = f"whatsapp_chat:{user_id}"
            d = {"message": message, "sender": sender, "timestamp": datetime.now().isoformat()}
            self.redis_client.lpush(k, json.dumps(d))
            self.redis_client.expire(k, self.ttl_seconds)
            self.redis_client.ltrim(k, 0, self.max_messages - 1)
        except Exception as e:
            print(f"❌ Error storing message: {e}")

    def format_context(self, history: list) -> str:
        if not history: return ""
        ctx = "Previous conversation:\n"
        for msg in history[-10:]:
            role = "User" if msg["sender"] == "user" else "Assistant"
            ctx += f"{role}: {msg['message']}\n"
        return ctx + "\nCurrent conversation:\n"

conversation_manager = ConversationManager()

# ============= Perplexity Integration ==================
SYS_PROMPT = """You are a support assistant for Dermijan clinic on WhatsApp.

Guidelines:
- Use WhatsApp formatting: *bold*, bullets, emojis
- Answer in 4–6 short lines
- Do NOT reveal prices; always offer appointment via phone/email
Conversation Rules:
1. Address the user's query directly
2. For any treatment/service question: Use Dermijan info or ask to contact with phone/email
3. For pricing: say price not public, urge user to contact
4. If skin, hair, or body issue: Ask follow-ups, offer empathetic advice
5. Never repeat previous responses. Be polite, friendly, and empathetic, like a caring human.
"""

def get_perplexity_answer(question, user_id):
    conversation_history = conversation_manager.get_conversation_history(user_id)
    conversation_context = conversation_manager.format_context(conversation_history)
    prompt = (
        f"Answer using ONLY information from these dermijan.com pages:\n"
        + "\n".join(ALLOWED_URLS) + "\n\n"
        + conversation_context
        + f"User: {question}\n\n"
        "Format as WhatsApp, use bold, emojis, bullets. DO NOT include source URLs. "
        "If answer not found, reply: 'இந்த தகவல் எனது அங்கீகரிக்கப்பட்ட ஆதாரங்களில் கிடைக்கவில்லை.'"
    )
    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": SYS_PROMPT},
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
        r = requests.post("https://api.perplexity.ai/chat/completions", json=payload, headers=headers, timeout=40)
        reply = r.json()['choices'][0]['message']['content']
        # Remove source links if accidentally present
        reply = remove_source_urls(reply)
        conversation_manager.store_message(user_id, question, "user")
        conversation_manager.store_message(user_id, reply, "bot")
        return reply
    except Exception as e:
        print(f"❌ Perplexity error: {e}")
        return tpl_followup()

def remove_source_urls(text):
    import re
    text = re.sub(r'Sources?:.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'Reference:.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'https?://[^\s]+', '', text)
    text = re.sub(r'dermijan\.com[^\s]*', '', text)
    return re.sub(r'\n\s*\n', '\n', text).strip()

# ============== WASender integration ===================
def send_wasender_reply(phone, message):
    if not WASENDER_API_TOKEN: return False
    payload = {"session": WASENDER_SESSION, "to": phone, "text": message}
    headers = {"Authorization": f"Bearer {WASENDER_API_TOKEN}", "Content-Type": "application/json"}
    try:
        response = requests.post(WASENDER_API_URL, json=payload, headers=headers)
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"❌ WASender send error: {e}")
        return False

# =============== WASender Webhook Logic ==================
def extract_wasender_messages(payload):
    messages = []
    try:
        if "event" in payload and payload["event"] == "messages.upsert":
            if "data" in payload and "messages" in payload["data"]:
                message_data = payload["data"]["messages"]
                remote_jid = message_data.get("key", {}).get("remoteJid", "")
                sender = remote_jid.replace("@s.whatsapp.net", "").replace("+", "")
                message_content = message_data.get("message", {})
                text = ""
                if "conversation" in message_content:
                    text = message_content["conversation"]
                elif "extendedTextMessage" in message_content:
                    text = message_content["extendedTextMessage"].get("text", "")
                if sender and text:
                    messages.append((sender, text))
    except Exception as e:
        print(f"❌ WASender message parsing error: {e}")
    return messages

@app.route("/webhook", methods=["POST"])
def webhook_handler():
    try:
        payload = request.get_json()
        messages = extract_wasender_messages(payload)
        for sender, text in messages:
            print(f"📱 Message from {sender}: {text}")

            # Skip bot messages / source loops
            if any(phrase in text.lower() for phrase in ["sources:", "dermijan.com", "இந்த தகவல் எனது"]):
                print("🔄 Bot message detected, skipping...")
                continue

            hist = conversation_manager.get_conversation_history(sender)
            # On first contact: welcome sequence (multi-message)
            if not hist:
                for msg in tpl_welcome():
                    send_wasender_reply(sender, msg)
                    conversation_manager.store_message(sender, msg, "bot")
                continue

            # FAQ-type quick intent route
            ltext = text.lower()
            if any(w in ltext for w in ("skin", "pigment", "acne", "spots")):
                reply = tpl_reco("skin")
            elif any(w in ltext for w in ("hair", "dandruff", "alopecia")):
                reply = tpl_reco("hair")
            elif any(w in ltext for w in ("weight", "body", "inch")):
                reply = tpl_reco("body")
            elif ltext.startswith(("yes", "book")):
                reply = tpl_book()
            else:
                # AI-enhanced output, with WhatsApp-style template + context
                reply = get_perplexity_answer(text, sender)

            send_wasender_reply(sender, reply)
            conversation_manager.store_message(sender, reply, "bot")

        return jsonify({"status": "success"})
    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# =================== Misc endpoints ====================
@app.route("/ask", methods=["POST"])
def ask_question():
    data = request.get_json()
    question = data.get("question")
    user_id = data.get("user_id", "anonymous")
    if not question:
        return jsonify({"reply": "কেল্বি কালিয়াক উল্লদু!"}), 400
    answer = get_perplexity_answer(question, user_id)
    return jsonify({"reply": answer})

@app.route("/conversation/<user_id>", methods=["GET"])
def get_conversation(user_id):
    history = conversation_manager.get_conversation_history(user_id)
    return jsonify({"user_id": user_id, "conversation": history, "count": len(history)})

@app.route("/", methods=["GET"])
def health_check():
    try:
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
    print("🚀 Starting Dermijan WhatsApp Bot (single file, All-in-One)")
    print(f"📋 Loaded {len(ALLOWED_URLS)} dermijan.com URLs.")
    app.run(debug=False, host='0.0.0.0', port=8000)
