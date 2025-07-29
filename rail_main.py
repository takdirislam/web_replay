# Dermijan Chatbot Enhanced User-Friendly Response System
# -------------------------------------------------------
# Flask application that integrates Perplexity API and WASender
# with emoji-rich, professionally friendly responses for users.

from flask import Flask, request, jsonify
import requests
import json
import os
import redis
from datetime import datetime

app = Flask(__name__)

# ────────────────────────────────────────────────────────────────
# 1. API & Redis Configuration
# ────────────────────────────────────────────────────────────────
PERPLEXITY_API_KEY = "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"
WASENDER_API_TOKEN = "37bf33ac1d6e4e6be8ae324373c2171400a1dd6183c6e501df646eb5f436ef6f"
WASENDER_SESSION = "TAKDIR"
WASENDER_API_URL = "https://wasenderapi.com/api/send-message"

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# ────────────────────────────────────────────────────────────────
# 2. Dermijan.com Allow-listed URLs
# ────────────────────────────────────────────────────────────────
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

# ────────────────────────────────────────────────────────────────
# 3. Conversation Manager
# ────────────────────────────────────────────────────────────────
class ConversationManager:
    def __init__(self):
        self.redis_client = redis_client
        self.ttl_seconds = 7 * 24 * 3600          # 7-day sliding window
        self.max_messages = 20                    # Keep last 20 msgs

    def get_conversation_history(self, user_id: str) -> list:
        """Fetch last N messages for a given user."""
        try:
            key = f"whatsapp_chat:{user_id}"
            msgs = self.redis_client.lrange(key, 0, -1)
            # Newest first in Redis, so reverse
            return [json.loads(m) for m in reversed(msgs)]
        except Exception as e:
            print(f"❌ History error for {user_id}: {e}")
            return []

    def store_message(self, user_id: str, message: str, sender: str = "user"):
        """Push a message & renew TTL with sliding window."""
        try:
            key = f"whatsapp_chat:{user_id}"
            self.redis_client.lpush(
                key,
                json.dumps(
                    {
                        "message": message,
                        "sender": sender,
                        "timestamp": datetime.now().isoformat(),
                    }
                ),
            )
            self.redis_client.expire(key, self.ttl_seconds)
            self.redis_client.ltrim(key, 0, self.max_messages - 1)
        except Exception as e:
            print(f"❌ Store error for {user_id}: {e}")

    def format_conversation_context(self, history: list) -> str:
        """Convert last 10 messages into LLM-friendly context."""
        if not history:
            return ""
        ctx = "Previous conversation:\n"
        for msg in history[-10:]:
            role = "User" if msg["sender"] == "user" else "Assistant"
            ctx += f"{role}: {msg['message']}\n"
        return ctx + "\nCurrent conversation:\n"


# Instantiate manager
conversation_manager = ConversationManager()

# ────────────────────────────────────────────────────────────────
# 4. Emoji Helpers & Response Formatter
# ────────────────────────────────────────────────────────────────
def get_service_emoji(text: str) -> str:
    """Return relevant emojis based on detected keywords."""
    t = text.lower()
    if any(w in t for w in ["skin", "acne", "fairness", "glow", "facial", "spot", "scar"]):
        return "✨💆‍♀️"
    if any(w in t for w in ["hair", "dandruff", "fall", "regrowth", "transplant"]):
        return "💇‍♀️💁‍♀️"
    if any(w in t for w in ["body", "weight", "inch", "toning", "sculpting"]):
        return "💪🏻📈"
    if any(w in t for w in ["aging", "anti-aging", "wrinkle", "age"]):
        return "⏰✨"
    if any(w in t for w in ["price", "cost", "rate", "fee"]):
        return "💰💯"
    if any(w in t for w in ["book", "appointment", "contact", "call"]):
        return "📞📅"
    return "🌟💡"


def format_response(reply: str, user_q: str) -> str:
    """Enhance reply with emojis, bold text, and line breaks."""
    # Prepend emoji header if absent
    emoji_hdr = get_service_emoji(user_q + " " + reply)
    if not any(e in reply[:10] for e in ["✨", "💆", "💇", "💪", "⏰", "🌟", "💡"]):
        reply = f"{emoji_hdr} {reply}"

    # Double line-break after full-stop for readability
    reply = reply.replace(". ", ".\n\n")

    # Highlight contact info
    reply = reply.replace("dermijanofficialcontact@gmail.com", "*dermijanofficialcontact@gmail.com*")
    reply = reply.replace("+91 9003444435", "*+91 9003444435*")

    return reply.strip()

# ────────────────────────────────────────────────────────────────
# 5. Perplexity Interaction
# ────────────────────────────────────────────────────────────────
def remove_source_urls(text: str) -> str:
    """Strip any inadvertent URLs or source sections."""
    import re

    text = re.sub(r"Sources?:.*$", "", text, flags=re.I | re.M)
    text = re.sub(r"Reference:.*$", "", text, flags=re.I | re.M)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"dermijan\.com\S*", "", text)
    text = re.sub(r"\n\s*\n", "\n", text)
    return text.strip()


def get_perplexity_answer(question: str, user_id: str) -> str:
    """Submit conversation-aware prompt to Perplexity & format reply."""
    print(f"📥 Q from {user_id}: {question}")

    history = conversation_manager.get_conversation_history(user_id)
    context = conversation_manager.format_conversation_context(history)

    prompt = (
        "🌟 Answer enthusiastically using ONLY information from these dermijan.com pages:\n"
        + "\n".join(ALLOWED_URLS)
        + "\n\n"
        + context
        + f"User: {question}\n\n"
        + "Instructions: Give a SHORT, engaging answer (4-6 lines max) with professional yet friendly tone. "
        + "Use relevant emojis, *bold* key info, create mild excitement. "
        + "Do NOT use outside information. Only the provided dermijan.com URLs. "
        + "If answer not found, reply: '✨ এই তথ্য আমার অনুমোদিত সোর্সে পাওয়া যায়নি। দয়া করে আমাদের টিমের সাথে যোগাযোগ করুন। 📞' "
        + "Do NOT include source URLs in your response. Keep it conversational, helpful and exciting!"
    )

    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a support assistant for a skin, hair, and body care clinic named *Dermijan*, "
                    "interacting with customers on WhatsApp.\n\n"
                    "**Guidelines:**\n"
                    "- Use WhatsApp formatting:\n"
                    "  - *Bold* for key terms, prices, and important info (asterisks)\n"
                    "  - Relevant emojis for each service category\n"
                    "  - Bullets (with hyphens) for lists\n"
                    "  - Line breaks for readability\n"
                    "  - Keep replies short (4–6 lines)\n\n"
                    "**Emoji Usage by Service:**\n"
                    "• Skin care: ✨💆‍♀️🌟💅\n"
                    "• Hair care: 💇‍♀️💁‍♀️🔥💫\n"
                    "• Body treatments: 💪🏻🏃‍♀️📈💯\n"
                    "• Anti-aging: ⏰🔄✨👑\n"
                    "• General: 💡🎉🌟💯\n\n"
                    "**Tone & Style:** Professional yet friendly, mildly urgent, exciting.\n"
                    "**Response Structure:**\n"
                    "1. Greeting + emoji\n"
                    "2. *Bold* key info\n"
                    "3. Bulleted benefits\n"
                    "4. CTA + contact info\n\n"
                    "**Conversation Rules:**\n"
                    "1. Address each query clearly & enthusiastically.\n"
                    "2. For missing info → ask to contact support.\n"
                    "3. Pricing format → 💰 *Price*: ₹XXXX …\n"
                    "4. For issues → ask follow-ups.\n"
                    "5. Never repeat identical responses; always suggest next step.\n",
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 1200,
        "temperature": 0.1,
    }

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post("https://api.perplexity.ai/chat/completions", json=payload, headers=headers)
        if response.status_code == 200:
            reply_raw = response.json()["choices"][0]["message"]["content"]
            reply = remove_source_urls(reply_raw)
            reply = format_response(reply, question)

            # Persist conversation
            conversation_manager.store_message(user_id, question, "user")
            conversation_manager.store_message(user_id, reply, "bot")
            return reply
        else:
            print(f"❌ Perplexity error {response.status_code}: {response.text}")
            return "মাফ করবেন, সার্ভারে আপাতত সমস্যা হচ্ছে। কিছুক্ষণ পরে চেষ্টা করুন। 🤖"
    except Exception as e:
        print(f"❌ Perplexity exception: {e}")
        return "মাফ করবেন, সিস্টেমে ত্রুটি হয়েছে। পরে চেষ্টা করুন। 🚧"

# ────────────────────────────────────────────────────────────────
# 6. WASender Utilities
# ────────────────────────────────────────────────────────────────
def extract_wasender_messages(payload: dict) -> list:
    """Return list of (sender_phone, text) tuples from WASender webhook."""
    msgs = []
    try:
        if payload.get("event") == "messages.upsert":
            m = payload.get("data", {}).get("messages", {})
            sender = m.get("key", {}).get("remoteJid", "").replace("@s.whatsapp.net", "").replace("+", "")
            text = ""
            if "conversation" in m.get("message", {}):
                text = m["message"]["conversation"]
            elif "extendedTextMessage" in m.get("message", {}):
                text = m["message"]["extendedTextMessage"].get("text", "")
            if sender and text:
                msgs.append((sender, text))
    except Exception as e:
        print(f"❌ WASender parse error: {e}")
    return msgs


def send_wasender_reply(to_phone: str, message: str) -> bool:
    """Send reply via WASender API."""
    if not WASENDER_API_TOKEN:
        print("❌ WASender token missing")
        return False
    payload = {"session": WASENDER_SESSION, "to": to_phone, "text": message}
    headers = {"Authorization": f"Bearer {WASENDER_API_TOKEN}", "Content-Type": "application/json"}
    try:
        res = requests.post(WASENDER_API_URL, json=payload, headers=headers)
        ok = res.status_code in (200, 201)
        print("✅" if ok else "❌", f"WASender reply to {to_phone}")
        return ok
    except Exception as e:
        print(f"❌ WASender send error: {e}")
        return False

# ────────────────────────────────────────────────────────────────
# 7. Flask Routes
# ────────────────────────────────────────────────────────────────
@app.route("/ask", methods=["POST"])
def ask_question():
    data = request.get_json()
    question = data.get("question")
    user_id = data.get("user_id", "anonymous")
    if not question:
        return jsonify({"reply": "প্রশ্ন প্রদান করুন।"}), 400
    answer = get_perplexity_answer(question, user_id)
    return jsonify({"reply": answer})


@app.route("/webhook", methods=["POST"])
def webhook_handler():
    try:
        payload = request.get_json()
        for sender, text in extract_wasender_messages(payload):
            # Skip bot-detected loops
            skip_phrases = ["Sources:", "dermijan.com", "এই তথ্য আমার অনুমোদিত"]
            if any(p.lower() in text.lower() for p in skip_phrases):
                continue
            reply = get_perplexity_answer(text, sender)
            send_wasender_reply(sender, reply)
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/conversation/<user_id>", methods=["GET"])
def get_conversation(user_id):
    hist = conversation_manager.get_conversation_history(user_id)
    return jsonify({"user_id": user_id, "conversation": hist, "count": len(hist)})


@app.route("/", methods=["GET"])
def health_check():
    try:
        redis_status = "connected" if redis_client.ping() else "disconnected"
    except Exception:
        redis_status = "error"
    return jsonify(
        {
            "status": "MCP Dermijan Server Running",
            "endpoints": ["/ask", "/webhook", "/conversation/<user_id>"],
            "allowed_urls_count": len(ALLOWED_URLS),
            "redis_status": redis_status,
            "features": {
                "emoji_responses": True,
                "dermijan_allowlist": True,
                "perplexity_integration": True,
                "wasender_webhook": True,
                "conversation_persistence": True,
                "sliding_window_ttl": "7 days",
                "max_messages_per_user": 20,
            },
        }
    )

# ────────────────────────────────────────────────────────────────
# 8. Main Entrypoint
# ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🚀 Starting MCP Dermijan Server with Redis...")
    print(f"📋 Loaded {len(ALLOWED_URLS)} allowed dermijan.com URLs")
    print("🔗 Endpoints: /ask (direct), /webhook (WhatsApp), /conversation/<user_id> (debug)")
    print("💾 Redis TTL: 7 days (sliding window)")
    app.run(debug=True, host="0.0.0.0", port=8000)
