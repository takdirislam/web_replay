from flask import Flask, request, jsonify
from datetime import datetime
import requests, json, os, redis, re

# ────────────────────────────────
# 1. Flask & Redis setup
# ────────────────────────────────
app = Flask(__name__)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# ────────────────────────────────
# 2. API credentials
# ────────────────────────────────
PERPLEXITY_API_KEY = "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"
WASENDER_API_TOKEN = "37bf33ac1d6e4e6be8ae324373c2171400a1dd6183c6e501df646eb5f436ef6f"
WASENDER_SESSION   = "TAKDIR"
WASENDER_API_URL   = "https://wasenderapi.com/api/send-message"

# ────────────────────────────────
# 3. Allow-listed Dermijan URLs
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
# 4. System prompt (ONE string)
# ────────────────────────────────
SYSTEM_PROMPT = (
    "You are a support assistant for *Dermijan*, a skin-, hair- and body-care clinic, "
    "chatting on WhatsApp.\n\n"
    "Guidelines:\n"
    "- Use WhatsApp *Bold* for key terms\n"
    "- Add relevant emojis per service\n"
    "- Bullet lists with hyphens; max 4-6 short lines\n"
    "- Maintain a professional yet friendly, mildly urgent tone\n\n"
    "Service Emojis:\n"
    "• Skin care: ✨💆‍♀️🌟💅  • Hair care: 💇‍♀️💁‍♀️🔥💫  • Body: 💪🏻📈  • Anti-aging: ⏰✨\n\n"
    "Response structure: Greeting + emoji → *Bold* info → bullets → CTA + contact\n"
    "Conversation rules: Missing info ⇒ ask user to contact support; pricing format ⇒ "
    "💰 *Price*: ₹XXXX (approx).\n"
)

# ────────────────────────────────
# 5. Conversation manager
# ────────────────────────────────
class ConversationManager:
    def __init__(self):
        self.ttl = 7 * 24 * 3600
        self.max_msgs = 20

    def _key(self, uid): return f"whatsapp_chat:{uid}"

    def get_history(self, uid):
        try:
            hist = self._fetch(uid)
            return [json.loads(m) for m in reversed(hist)]
        except Exception as e:
            print("❌ history", e); return []

    def _fetch(self, uid):
        return redis_client.lrange(self._key(uid), 0, -1)

    def store(self, uid, msg, who="user"):
        try:
            redis_client.lpush(self._key(uid),
                               json.dumps({"message": msg,
                                           "sender": who,
                                           "ts": datetime.now().isoformat()}))
            redis_client.ltrim(self._key(uid), 0, self.max_msgs-1)
            redis_client.expire(self._key(uid), self.ttl)
        except Exception as e:
            print("❌ store", e)

    def context(self, hist):
        if not hist: return ""
        ctx = "Previous conversation:\n"
        for m in hist[-10:]:
            role = "User" if m["sender"] == "user" else "Assistant"
            ctx += f"{role}: {m['message']}\n"
        return ctx + "\nCurrent conversation:\n"

mgr = ConversationManager()

# ────────────────────────────────
# 6. Emoji & formatting helpers
# ────────────────────────────────
def pick_emoji(txt):
    t = txt.lower()
    if any(k in t for k in ["skin", "acne", "facial", "scar"]):          return "✨💆‍♀️"
    if any(k in t for k in ["hair", "dandruff", "transplant"]):          return "💇‍♀️💁‍♀️"
    if any(k in t for k in ["body", "weight", "toning", "sculpt"]):      return "💪🏻📈"
    if any(k in t for k in ["aging", "wrinkle"]):                        return "⏰✨"
    if any(k in t for k in ["price", "cost", "rate"]):                   return "💰💯"
    return "🌟💡"

def format_reply(raw, q):
    em = pick_emoji(q + " " + raw)
    if em not in raw[:5]:
        raw = f"{em} {raw}"
    raw = raw.replace(". ", ".\n\n")
    raw = raw.replace("dermijanofficialcontact@gmail.com",
                      "*dermijanofficialcontact@gmail.com*")
    raw = raw.replace("+91 9003444435", "*+91 9003444435*")
    return raw.strip()

# ────────────────────────────────
# 7. Perplexity client
# ────────────────────────────────
PPLX_URL = "https://api.perplexity.ai/chat/completions"
def scrub(text):
    text = re.sub(r"Sources?:.*$", "", text, flags=re.I|re.M)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"dermijan\.com\S*", "", text)
    return re.sub(r"\n\s*\n", "\n", text).strip()

def _debug_messages(payload):
    for i, m in enumerate(payload["messages"]):
        print(i, type(m["content"]))

def ask_pplx(question, uid):
    hist  = mgr.get_history(uid)
    ctx   = mgr.context(hist)
    user_prompt = (
        "🌟 Answer enthusiastically using ONLY these Dermijan pages:\n"
        + "\n".join(ALLOWED_URLS) + "\n\n"
        + ctx + f"User: {question}\n\n"
        "Instr: 4-6 lines, emojis, *bold* key info, friendly. "
        "If not found, reply: '✨ Information not found, contact support.📞'"
    )

    payload = {
        "model": "sonar-pro",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_prompt}
        ],
        "max_tokens": 1000,
        "temperature": 0.1
    }

    _debug_messages(payload)           # type-check → all should be <class 'str'>

    headers = {"Authorization": f"Bearer {PERPLEXITY_API_KEY}",
               "Content-Type": "application/json"}

    try:
        r = requests.post(PPLX_URL, json=payload, headers=headers, timeout=30)
        if r.status_code == 200:
            ans = scrub(r.json()["choices"][0]["message"]["content"])
            ans = format_reply(ans, question)
            mgr.store(uid, question, "user")
            mgr.store(uid, ans, "bot")
            return ans
        print("❌ PPLX", r.status_code, r.text)
        return "Sorry, the server is currently experiencing problems. Please try again later.। 🤖"
    except Exception as e:
        print("❌ PPLX ex", e)
        return "Sorry, the server is currently experiencing problems. Please try again later.। 🚧"

# ────────────────────────────────
# 8. WASender utilities
# ────────────────────────────────
def parse_wasender(payload):
    out = []
    try:
        if payload.get("event") == "messages.upsert":
            m = payload["data"]["messages"]
            sender = m["key"]["remoteJid"].split("@")[0].lstrip("+")
            msg    = m["message"].get("conversation") or \
                     m["message"].get("extendedTextMessage", {}).get("text", "")
            if sender and msg: out.append((sender, msg))
    except Exception as e:
        print("❌ parse_wasender", e)
    return out

def send_wasender(to, text):
    if not WASENDER_API_TOKEN: return False
    res = requests.post(WASENDER_API_URL,
                        headers={"Authorization": f"Bearer {WASENDER_API_TOKEN}",
                                 "Content-Type": "application/json"},
                        json={"session": WASENDER_SESSION, "to": to, "text": text})
    ok = res.status_code in (200, 201)
    print("✅" if ok else "❌", "send_wasender", res.status_code)
    return ok

# ────────────────────────────────
# 9. Flask routes
# ────────────────────────────────
@app.post("/ask")
def ask():
    data = request.get_json(force=True)
    q    = data.get("question")
    uid  = data.get("user_id", "anon")
    if not q: return jsonify({"reply": "Ask Question।"}), 400
    return jsonify({"reply": ask_pplx(q, uid)})

@app.post("/webhook")
def webhook():
    for sender, txt in parse_wasender(request.get_json(force=True)):
        if any(k in txt.lower() for k in ["sources:", "dermijan.com"]): continue
        ans = ask_pplx(txt, sender)
        send_wasender(sender, ans)
    return jsonify({"status": "ok"})

@app.get("/conversation/<uid>")
def conv(uid):
    hist = mgr.get_history(uid)
    return jsonify({"user": uid, "count": len(hist), "conversation": hist})

@app.get("/")
def health():
    try: rd = "connected" if redis_client.ping() else "disconnected"
    except: rd = "error"
    return jsonify({"status": "running", "redis": rd,
                    "allowed_urls": len(ALLOWED_URLS)})

# ────────────────────────────────
# 10. Main
# ────────────────────────────────
if __name__ == "__main__":
    print("🚀 Dermijan server up ⎯ http://0.0.0.0:8000")
    app.run(host="0.0.0.0", port=8000, debug=True)
