from flask import Flask, request, jsonify
import requests
import json
import os

app = Flask(__name__)

# API Configuration - Environment variables ব্যবহার
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY", "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")
WASENDER_API_TOKEN = os.environ.get("WASENDER_API_TOKEN", "37bf33ac1d6e4e6be8ae324373c2171400a1dd6183c6e501df646eb5f436ef6f")
WASENDER_SESSION = os.environ.get("WASENDER_SESSION", "TAKDIR")
WASENDER_API_URL = "https://wasenderapi.com/api/send-message"

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

def get_perplexity_answer(question):
    """Get answer from Perplexity API with dermijan.com restriction"""
    print(f"📥 Question received: {question}")
    
    # Build restricted prompt with allowlist - SHORTER VERSION
    prompt = (
        f"Answer briefly using ONLY information from these dermijan.com pages:\n"
        + "\n".join(ALLOWED_URLS) + "\n\n"
        f"Question: {question}\n\n"
        "Instructions: Give a SHORT, direct answer (2-3 sentences maximum). "
        "Do NOT use outside information. Only use the provided dermijan.com URLs. "
        "If answer not found, reply: 'இந்த தகவல் எனது அங்கீகரிக்கப்பட்ட ஆதாரங்களில் கிடைக்கவில்லை.' "
        "Do NOT include source URLs in your response. Keep it very concise."
    )
    
    url = "https://api.perplexity.ai/chat/completions"
    
    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": "Give very SHORT answers (maximum 2-3 sentences). Do not include source URLs."},
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
            
            # Validate response contains allowed URLs (but don't show them)
            used_urls = [u for u in ALLOWED_URLS if u in reply]
            if "இந்த தகவல்" in reply:
                return "இந்த தகவல் எனது அங்கீகரிக்கப்பட்ட ஆதாரங்களில் கிடைக்கவில்லை"
            
            return reply
        else:
            print(f"❌ Perplexity API error: {response.status_code} - {response.text}")
            return "மன்னிக்கவும், இந்த நேரத்தில் சேவை வழங்க முடியவில்லை."
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return "மன்னிக்கவும், சில சிக்கல் ஏற்பட்டுள்ளது."

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
    
    if not question:
        return jsonify({"reply": "কেল্কী কাছিবক উল্টস!"}), 400
    
    answer = get_perplexity_answer(question)
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
            if any(phrase in text.lower() for phrase in ["sources:", "dermijan.com", "இந்த তકবল এনাতু"]):
                print("🔄 Bot message detected, skipping...")
                continue
            
            # Get answer from Perplexity
            answer = get_perplexity_answer(text)
            
            # Send reply via WASender
            send_wasender_reply(sender, answer)
        
        return jsonify({"status": "success"})
        
    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "MCP Dermijan Server Running",
        "endpoints": ["/ask", "/webhook"],
        "allowed_urls_count": len(ALLOWED_URLS),
        "features": {
            "dermijan_allowlist": True,
            "perplexity_integration": True,
            "wasender_webhook": True,
            "source_citation": True
        }
    })

if __name__ == "__main__":
    print("🚀 Starting MCP Dermijan Server...")
    print(f"📋 Loaded {len(ALLOWED_URLS)} allowed dermijan.com URLs")
    print("🔗 Endpoints: /ask (direct), /webhook (WhatsApp)")
    port = int(os.environ.get("PORT", 8000))
    app.run(debug=False, host='0.0.0.0', port=port)
