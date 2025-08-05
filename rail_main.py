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
WAHA_API_KEY = "ckr7eqa_MKE6teg2xef"
WAHA_BASE_URL = os.getenv("WAHA_BASE_URL", "https://waha.peacockindia.in")
WAHA_SESSION = os.getenv("WAHA_SESSION", "DERMIJAN_BOT")
WAHA_SEND_TEXT_URL = f"{WAHA_BASE_URL}/api/sendText"


print(f"🔗 WAHA Configuration: {WAHA_BASE_URL} (Session: {WAHA_SESSION})")


# ────────────────────────────────
# NEW: Complete User Data Extraction System
# ────────────────────────────────
class UserDataExtractor:
    def __init__(self):
        # Complete Name Detection Patterns - English & Tamil
        self.name_patterns = {
            'english': [
                r'my name is ([A-Za-z\s]{2,30})',
                r'i am ([A-Za-z\s]{2,30})',
                r'this is ([A-Za-z\s]{2,30})',
                r'i\'m ([A-Za-z\s]{2,30})',
                r'call me ([A-Za-z\s]{2,30})',
                r'myself ([A-Za-z\s]{2,30})',
                r'name ([A-Za-z\s]{2,30})',
                r'they call me ([A-Za-z\s]{2,30})',
                r'you can call me ([A-Za-z\s]{2,30})',
                r'i go by ([A-Za-z\s]{2,30})',
                r'i am known as ([A-Za-z\s]{2,30})',
                r'my name\'s ([A-Za-z\s]{2,30})',
                r'name is ([A-Za-z\s]{2,30})',
                r'i\'m called ([A-Za-z\s]{2,30})',
                r'people call me ([A-Za-z\s]{2,30})',
                r'known as ([A-Za-z\s]{2,30})',
                r'it\'s ([A-Za-z\s]{2,30})',
                r'the name is ([A-Za-z\s]{2,30})',
                r'hi i\'m ([A-Za-z\s]{2,30})',
                r'hello i\'m ([A-Za-z\s]{2,30})',
                r'i am ([A-Za-z\s]{2,30}) here',
                r'speaking ([A-Za-z\s]{2,30})',
                r'this is ([A-Za-z\s]{2,30}) speaking',
                r'my friends call me ([A-Za-z\s]{2,30})',
                r'everyone calls me ([A-Za-z\s]{2,30})',
                r'just call me ([A-Za-z\s]{2,30})',
                r'i prefer ([A-Za-z\s]{2,30})',
                r'i go by the name ([A-Za-z\s]{2,30})',
                r'introduced as ([A-Za-z\s]{2,30})',
                r'commonly known as ([A-Za-z\s]{2,30})',
                r'nickname is ([A-Za-z\s]{2,30})',
                r'nick name ([A-Za-z\s]{2,30})',
                r'full name is ([A-Za-z\s]{2,30})',
                r'first name is ([A-Za-z\s]{2,30})',
                r'last name is ([A-Za-z\s]{2,30})',
                r'surname is ([A-Za-z\s]{2,30})',
                r'family name is ([A-Za-z\s]{2,30})',
                r'given name is ([A-Za-z\s]{2,30})',
                r'middle name is ([A-Za-z\s]{2,30})',
                r'i\'m ([A-Za-z\s]{2,30}) by name',
                r'named ([A-Za-z\s]{2,30})',
                r'christened ([A-Za-z\s]{2,30})',
                r'baptized as ([A-Za-z\s]{2,30})',
                r'born ([A-Za-z\s]{2,30})',
                r'legally ([A-Za-z\s]{2,30})',
                r'officially ([A-Za-z\s]{2,30})',
                r'registered as ([A-Za-z\s]{2,30})',
                r'formally ([A-Za-z\s]{2,30})',
                r'professionally known as ([A-Za-z\s]{2,30})',
                r'stage name is ([A-Za-z\s]{2,30})',
                r'pen name is ([A-Za-z\s]{2,30})',
                r'alias ([A-Za-z\s]{2,30})',
                r'aka ([A-Za-z\s]{2,30})',
                r'also known as ([A-Za-z\s]{2,30})'
            ],
            'tamil': [
                r'என் பெயர் ([^\s]{2,30})',
                r'நான் ([^\s]{2,30})',
                r'எனக்கு ([^\s]{2,30}) என்று பெயர்',
                r'பெயர் ([^\s]{2,30})',
                r'என்னை ([^\s]{2,30}) என்று அழைக்கவும்',
                r'என்னை ([^\s]{2,30}) என்று அழைக்கலாம்',
                r'நான் ([^\s]{2,30}) தான்',
                r'என்னுடைய பெயர் ([^\s]{2,30})',
                r'என் பெயர் ([^\s]{2,30}) என்று',
                r'எல்லோரும் என்னை ([^\s]{2,30}) என்று அழைக்கிறார்கள்',
                r'மக்கள் என்னை ([^\s]{2,30}) என்று அழைக்கிறார்கள்',
                r'நண்பர்கள் என்னை ([^\s]{2,30}) என்று அழைக்கிறார்கள்',
                r'வணக்கம் நான் ([^\s]{2,30})',
                r'ஹலோ நான் ([^\s]{2,30})',
                r'என் முழு பெயர் ([^\s]{2,30})',
                r'என் முதல் பெயர் ([^\s]{2,30})',
                r'என் கடைசி பெயர் ([^\s]{2,30})',
                r'என் குடும்ப பெயர் ([^\s]{2,30})',
                r'என் வீட்டு பெயர் ([^\s]{2,30})',
                r'என் சிறு பெயர் ([^\s]{2,30})',
                r'என் செல்லப் பெயர் ([^\s]{2,30})',
                r'என் அசல் பெயர் ([^\s]{2,30})',
                r'என் உண்மையான பெயர் ([^\s]{2,30})',
                r'என் பதிவு பெயர் ([^\s]{2,30})',
                r'என் அதிகாரப்பூர்வ பெயர் ([^\s]{2,30})',
                r'என் சட்டப்படி பெயர் ([^\s]{2,30})',
                r'என் நடிப்பு பெயர் ([^\s]{2,30})',
                r'என் எழுத்தாளர் பெயர் ([^\s]{2,30})',
                r'என் மாற்று பெயர் ([^\s]{2,30})',
                r'என் வேறு பெயர் ([^\s]{2,30})',
                r'என்னை ([^\s]{2,30}) என்றும் அழைக்கிறார்கள்',
                r'பொதுவாக ([^\s]{2,30}) என்று அழைக்கப்படுகிறேன்',
                r'என் பிறப்புப் பெயர் ([^\s]{2,30})',
                r'என் குழந்தைப் பெயர் ([^\s]{2,30})',
                r'என் இளமைப் பெயர் ([^\s]{2,30})',
                r'என் ஆரம்பப் பெயர் ([^\s]{2,30})',
                r'என் மூலப் பெயர் ([^\s]{2,30})',
                r'([^\s]{2,30}) என்று அழைக்கவும்',
                r'([^\s]{2,30}) என்று சொல்லுங்கள்',
                r'([^\s]{2,30}) என்று பெயர் வைத்திருக்கிறார்கள்',
                r'([^\s]{2,30}) என்பது என் பெயர்',
                r'([^\s]{2,30}) என்று தான் பெயர்',
                r'([^\s]{2,30}) என்று அறியப்படுகிறேன்',
                r'([^\s]{2,30}) என்று பிரபலம்',
                r'([^\s]{2,30}) என்கிற பெயரில்',
                r'([^\s]{2,30}) என்று வைத்திருக்கிறார்கள்',
                r'([^\s]{2,30}) என்று அழைக்கப்படுகிறேன்',
                r'([^\s]{2,30}) என்று நாமகரணம்',
                r'([^\s]{2,30}) என்கிற பெயரில் பிறந்தேன்',
                r'([^\s]{2,30}) என்று ஞானஸ்னானம்',
                r'([^\s]{2,30}) என்று தீர்த்தம்',
                r'([^\s]{2,30}) என்னும் பெயரில்'
            ]
        }
        
        # Complete 186 Medical Problems Database - English & Tamil
        self.problem_keywords = {
            'acne_problems': {
                'english': [
                    'acne', 'acne scarring', 'acne scars', 'cystic acne', 'blackheads', 
                    'whiteheads', 'comedones', 'post-acne marks'
                ],
                'tamil': [
                    'முகப்பருக்கள்', 'முகப்பரு தழும்புகள்', 'முகப்பரு வடுக்கள்', 
                    'கரும்புள்ளிகள்'
                ]
            },
            'skin_pigmentation': {
                'english': [
                    'age spots', 'dark spots', 'melasma', 'chloasma', 'hyperpigmentation',
                    'post-inflammatory hyperpigmentation', 'pigmentation', 'skin discoloration',
                    'uneven skin tone', 'liver spots', 'sun spots', 'freckles',
                    'skin brightening', 'skin fairness', 'skin whitening', 'blemishes'
                ],
                'tamil': [
                    'வயது புள்ளிகள்', 'கருந்திட்டு', 'கறைகள்', 'நிறமிப்பு', 
                    'தோல் வெளுப்பு', 'சீரற்ற தோல் நிறம்', 'தோல் நியாயம்', 
                    'தோல் பிரகாசமாக்கல்'
                ]
            },
            'aging_wrinkles': {
                'english': [
                    'aging', 'ageing', 'wrinkles', 'fine lines', 'deep lines', 
                    'crow\'s feet', 'laugh lines', 'forehead lines', 'neck wrinkles',
                    'photo-aging', 'natural anti-aging', 'collagen loss', 'skin laxity',
                    'sagging skin', 'loose skin', 'elasticity loss', 'contractures'
                ],
                'tamil': [
                    'முதுமை', 'வயதாகுதல்', 'சுருக்கங்கள்', 'ஆழமான கோடுகள்',
                    'கழுத்து சுருக்கங்கள்', 'தளர்வான தோல்', 'தொங்கும் தோல்',
                    'கொலாஜன் இழப்பு', 'நெகிழ்வுத்தன்மை இழப்பு', 'சுருக்கங்கள்'
                ]
            },
            'hair_problems': {
                'english': [
                    'hair fall', 'hair loss', 'baldness', 'alopecia areata', 
                    'alopecia totalis', 'alopecia universalis', 'male pattern hair loss',
                    'female pattern hair loss', 'hair thinning', 'telogen effluvium',
                    'anagen effluvium', 'traction alopecia', 'trichotillomania',
                    'dandruff', 'hair regrowth solutions', 'hair restoration',
                    'hair transplant', 'hair transplantation', 'baby hair regrowth',
                    'central centrifugal cicatricial alopecia', 'hirsutism'
                ],
                'tamil': [
                    'முடி உதிர்தல்', 'முடி இழப்பு', 'வழுக்கை', 'பொடுகு', 
                    'முடி மெல்லிதல்', 'முடி மீள்வளர்ச்சி', 'முடி மறுசீரமைப்பு',
                    'முடி மாற்று அறுவை சிகிச்சை', 'முடி இடமாற்றம்', 'குழந்தை முடி மீள்வளர்ச்சி'
                ]
            },
            'skin_conditions': {
                'english': [
                    'eczema', 'atopic dermatitis', 'seborrheic dermatitis', 'contact dermatitis',
                    'irritant dermatitis', 'perioral dermatitis', 'dermatitis herpetiformis',
                    'psoriasis', 'rosacea', 'vitiligo', 'leukoderma', 'urticaria',
                    'keratosis pilaris', 'seborrheic keratosis', 'ichthyosis', 'dermatitis',
                    'allergic dermatitis', 'stasis dermatitis'
                ],
                'tamil': [
                    'அரிக்கும்தோல்வலி', 'அட்டோபிக் டெர்மடைடிஸ்', 'தோல்வலி',
                    'சொரியாசிஸ்', 'வெண்குஷ்டம்', 'சிவத்தல்', 'ஒவ்வாமை தோல்வலி'
                ]
            },
            'body_contouring': {
                'english': [
                    'body contouring', 'body sculpting', 'body toning', 'figure correction',
                    'cellulite', 'stretch marks', 'inch loss', 'weight management',
                    'body fat', 'subcutaneous fat', 'double chin', 'lipo lab'
                ],
                'tamil': [
                    'உடல் வடிவமைப்பு', 'உடல் செதுக்கல்', 'உடல் இறுக்கம்',
                    'உருவ திருத்தம்', 'நீட்சி அடையாளங்கள்', 'அங்குல இழப்பு',
                    'எடை மேலாண்மை', 'உடல் கொழுப்பு', 'இரட்டை கன்னம்'
                ]
            },
            'skin_texture': {
                'english': [
                    'enlarged pores', 'rough skin texture', 'dry skin', 'oily skin',
                    'combination skin', 'sensitive skin', 'skin polishing',
                    'skin rejuvenation', 'flawless skin', 'smooth skin', 'skin glow enhancement',
                    'skin thinning', 'xerosis'
                ],
                'tamil': [
                    'விரிவாக்கப்பட்ட துளைகள்', 'கரடுமுரடான தோல் அமைப்பு',
                    'வறண்ட தோல்', 'எண்ணெய் தோல்', 'கலப்பு தோல்',
                    'உணர்திறன் தோல்', 'தோல் மெருகூட்டல்', 'குறைபாடற்ற தோல்',
                    'மென்மையான தோல்', 'தோல் மெல்லிதல்'
                ]
            },
            'scars_marks': {
                'english': [
                    'scarring', 'deep scars', 'hypertrophic scars', 'keloids',
                    'post-inflammatory changes', 'skin tags', 'moles', 'suspicious moles',
                    'warts', 'vascular lesions', 'broken capillaries', 'spider veins',
                    'telangiectasia'
                ],
                'tamil': [
                    'வடு ஏற்படுதல்', 'ஆழமான வடுக்கள்', 'தோல் குறிகள்',
                    'திமில்கள்', 'மரு', 'சந்தேகத்திற்குரிய திமில்கள்',
                    'உடைந்த நுண்குழல்கள்', 'சிலந்தி நரம்புகள்'
                ]
            },
            'infections_allergies': {
                'english': [
                    'bacterial infections', 'fungal infections', 'viral infections',
                    'nail infections', 'allergic reactions', 'allergic dermatitis',
                    'infection', 'inflammation', 'skin irritation', 'burning sensation',
                    'swelling', 'redness', 'nail dystrophy', 'nail psoriasis',
                    'ingrown nails', 'molluscum contagiosum'
                ],
                'tamil': [
                    'பாக்டீரியா தொற்றுகள்', 'பூஞ்சை தொற்றுகள்', 'வைரஸ் தொற்றுகள்',
                    'நகம் தொற்றுகள்', 'ஒவ்வாமை எதிர்வினைகள்', 'ஒவ்வாமை தோல்வலி',
                    'தொற்று', 'வீக்கம்', 'தோல் எரிச்சல்', 'எரியும் உணர்வு',
                    'வீக்கம்', 'சிவப்பு'
                ]
            },
            'sun_damage': {
                'english': [
                    'sun damage', 'sunburn', 'environmental damage', 'excess melanin',
                    'melanin control', 'summer skincare', 'winter skincare'
                ],
                'tamil': [
                    'சூரிய சேதம்', 'வெயில் காயம்', 'சுற்றுச்சூழல் சேதம்',
                    'அதிக மெலனின்', 'கோடைகால தோல் பராமரிப்பு', 'குளிர்கால தோல் பராமரிப்பு'
                ]
            },
            'specialized_treatments': {
                'english': [
                    'laser hair removal complications', 'laser complications', 'derma roller treatment',
                    'prp treatment', 'platelet rich plasma', 'plant plasma treatment',
                    'kojic acid treatment', 'vitamin therapy', 'hydrocortisone treatment',
                    'stem cell technology', 'korean skincare', 'medi facials',
                    'face mask treatments', 'non-surgical treatments', 'surgical treatments',
                    'treatment side effects', 'inflammation treatment'
                ],
                'tamil': [
                    'டெர்மா ரோலர் சிகிச்சை', 'கோஜிக் அமில சிகிச்சை',
                    'கொரிய தோல் பராமரிப்பு', 'வைட்டமின் சிகிச்சை',
                    'அறுவைசிகிச்சையற்ற சிகிச்சைகள்', 'அறுவைசிகிச்சை சிகிச்சைகள்',
                    'வீக்கத்துக்கு பிந்தைய மாற்றங்கள்', 'வீக்கத்துக்கு பிந்தைய மிகைநிறமிப்பு'
                ]
            },
            'special_conditions': {
                'english': [
                    'autoimmune diseases', 'hormonal imbalances', 'hormonal abnormalities',
                    'genetic disorders', 'hirsutism', 'unwanted hair removal',
                    'precancerous lesions', 'skin cancer screening', 'basal cell carcinoma',
                    'squamous cell carcinoma', 'melanoma', 'lupus', 'scleroderma',
                    'systemic sclerosis', 'pemphigoid', 'pemphigus', 'leprosy',
                    'sexually transmitted infections', 'burns', 'blunt trauma injuries'
                ],
                'tamil': [
                    'தன்னுயிர் எதிர்ப்பு நோய்கள்', 'ஹார்மோன் அசாதாரணங்கள்',
                    'ஹார்மோன் ஏற்றத்தாழ்வுகள்', 'மரபணு கோளாறுகள்',
                    'தேவையற்ற முடி அகற்றல்', 'தீக்காயங்கள்', 'முட்டு காயங்கள்'
                ]
            },
            'aesthetic_procedures': {
                'english': [
                    'aesthetic procedures', 'cosmetic procedures', 'non-surgical treatments',
                    'surgical treatments', 'facelifts', 'facial contouring', 'medi facials',
                    'face mask treatments', 'wedding skincare', 'diet for skin',
                    'collagen production', 'under eye circles', 'dark circles'
                ],
                'tamil': [
                    'அழகியல் நடைமுறைகள்', 'அறுவைசிகிச்சையற்ற சிகிச்சைகள்',
                    'அறுவைசிகிச்சை சிகிச்சைகள்', 'முக வடிவமைப்பு', 'முகம் இறுக்கல்',
                    'முக மாஸ்க் சிகிச்சைகள்', 'திருமண தோல் பராமரிப்பு', 'தோலுக்கான உணவு',
                    'கொலாஜன் உற்பத்தி', 'கண்களுக்கு கீழே கருவளையங்கள்'
                ]
            }
        }

    def extract_name(self, message):
        """Extract user name from message"""
        message_clean = message.strip()
        
        # Try English patterns
        for pattern in self.name_patterns['english']:
            match = re.search(pattern, message_clean, re.IGNORECASE)
            if match:
                name = match.group(1).strip().title()
                name = re.sub(r'\s+', ' ', name)
                if 2 <= len(name) <= 30 and re.match(r'^[A-Za-z\s]+$', name):
                    return name
        
        # Try Tamil patterns
        for pattern in self.name_patterns['tamil']:
            match = re.search(pattern, message_clean)
            if match:
                name = match.group(1).strip()
                if 2 <= len(name) <= 30:
                    return name
        
        return None

    def extract_problems(self, message):
        """Extract medical problems from message"""
        detected_problems = []
        message_lower = message.lower()
        
        for category, languages in self.problem_keywords.items():
            # English keywords
            for keyword in languages['english']:
                if keyword.lower() in message_lower:
                    detected_problems.append({
                        'problem': keyword,
                        'category': category,
                        'language': 'english',
                        'confidence': 'high',
                        'detected_at': datetime.now().isoformat()
                    })
            
            # Tamil keywords
            for keyword in languages['tamil']:
                if keyword in message:
                    detected_problems.append({
                        'problem': keyword,
                        'category': category,
                        'language': 'tamil',
                        'confidence': 'high',
                        'detected_at': datetime.now().isoformat()
                    })
        
        # Remove duplicates
        unique_problems = []
        seen = set()
        for problem in detected_problems:
            key = f"{problem['problem']}_{problem['category']}"
            if key not in seen:
                seen.add(key)
                unique_problems.append(problem)
        
        return unique_problems


class PermanentUserStorage:
    def __init__(self, redis_client):
        self.redis_client = redis_client
    
    def save_user_name(self, phone, name):
        """Save user name permanently"""
        key = f"user_profile:{phone}:name"
        
        # Check if name already exists
        existing_data = self.redis_client.get(key)
        if existing_data:
            existing_name = json.loads(existing_data)['name']
            if existing_name.lower() == name.lower():
                print(f"📝 Name already exists for {phone}: {name}")
                return False
        
        user_data = {
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "source": "chat_extraction",
            "phone": phone
        }
        self.redis_client.set(key, json.dumps(user_data))
        print(f"✅ Saved name: {name} for user: {phone}")
        return True
    
    def save_user_problems(self, phone, problems):
        """Save user problems permanently"""
        if not problems:
            return 0
            
        saved_count = 0
        key = f"user_profile:{phone}:problems"
        
        # Get existing problems to avoid duplicates
        existing_problems = self.redis_client.lrange(key, 0, -1)
        existing_set = set()
        for existing in existing_problems:
            existing_data = json.loads(existing)
            existing_set.add(f"{existing_data['problem']}_{existing_data['category']}")
        
        for problem in problems:
            problem_key = f"{problem['problem']}_{problem['category']}"
            if problem_key not in existing_set:
                problem_data = {
                    "problem": problem['problem'],
                    "category": problem['category'],
                    "language": problem['language'],
                    "timestamp": datetime.now().isoformat(),
                    "status": "active",
                    "phone": phone
                }
                self.redis_client.lpush(key, json.dumps(problem_data))
                saved_count += 1
        
        if saved_count > 0:
            print(f"✅ Saved {saved_count} new problems for user: {phone}")
        return saved_count
    
    def get_user_profile_summary(self, phone):
        """Get complete user profile"""
        # Get name
        name_key = f"user_profile:{phone}:name"
        name_data = self.redis_client.get(name_key)
        name = json.loads(name_data)['name'] if name_data else None
        
        # Get problems
        problems_key = f"user_profile:{phone}:problems"
        problems_data = self.redis_client.lrange(problems_key, 0, -1)
        problems = [json.loads(p) for p in problems_data]
        
        # Categorize problems
        categorized = {}
        for problem in problems:
            category = problem['category']
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(problem)
        
        return {
            "name": name,
            "problems": problems,
            "categorized_problems": categorized,
            "total_problems": len(problems),
            "has_profile": bool(name or problems)
        }

    def generate_personalized_greeting(self, phone):
        """Generate personalized greeting based on saved profile"""
        profile = self.get_user_profile_summary(phone)
        
        if not profile['has_profile']:
            return None
        
        greeting_parts = []
        
        # Add name if available
        if profile['name']:
            greeting_parts.append(f"Hello {profile['name']}!")
        else:
            greeting_parts.append("Hello!")
        
        # Add problem-based context
        if profile['problems']:
            recent_problems = profile['problems'][:2]
            categories = list(set([p['category'] for p in recent_problems]))
            
            if 'acne_problems' in categories:
                greeting_parts.append("I see you've been interested in acne treatments.")
            elif 'hair_problems' in categories:
                greeting_parts.append("I see you've been interested in hair care solutions.")
            elif 'skin_pigmentation' in categories:
                greeting_parts.append("I see you've been interested in skin pigmentation treatments.")
            elif 'body_contouring' in categories:
                greeting_parts.append("I see you've been interested in body contouring treatments.")
            else:
                greeting_parts.append("I see you've been interested in our treatments.")
            
            greeting_parts.append("How can I help you today?")
        else:
            greeting_parts.append("How can I assist you today?")
        
        return " ".join(greeting_parts)


# Initialize extractors
extractor = UserDataExtractor()
storage = PermanentUserStorage(redis_client)


def process_message_with_extraction(phone, message):
    """Process message and extract/save user data"""
    extraction_result = {
        "name_extracted": None,
        "problems_extracted": [],
        "name_saved": False,
        "problems_saved": 0
    }
    
    try:
        # Extract name
        extracted_name = extractor.extract_name(message)
        if extracted_name:
            extraction_result["name_extracted"] = extracted_name
            extraction_result["name_saved"] = storage.save_user_name(phone, extracted_name)
        
        # Extract problems
        extracted_problems = extractor.extract_problems(message)
        if extracted_problems:
            extraction_result["problems_extracted"] = extracted_problems
            extraction_result["problems_saved"] = storage.save_user_problems(phone, extracted_problems)
        
    except Exception as e:
        print(f"❌ Extraction error for {phone}: {e}")
    
    return extraction_result


def detect_greeting_message(text):
    """Detect if message is a greeting"""
    greeting_keywords = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']
    tamil_greetings = ['வணக்கம்', 'ஹாய்', 'ஹலோ']
    
    text_lower = text.lower().strip()
    
    return (text_lower in greeting_keywords or 
            any(keyword in text_lower for keyword in greeting_keywords) or
            any(tamil_word in text for tamil_word in tamil_greetings) or
            len(text.strip()) <= 10 and any(greet in text_lower for greet in ['hi', 'hello', 'hey']))


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
- Tamil: "அப்பாய்ன்ட்மென்ட் புக் செய়্য, தயவুசெয়্து এঙ্গळৈ +91 9003444435 இল் আযৈক্কৱুম্, এঙ্গळ् তொডর্বু কুযু ৱিরৈভিল্ উঙ্গळৈ তொডর্বু কোল্লুম্।"


Remember: Apply research-backed formatting consistently. Every response should be scannable, mobile-friendly, and follow proven UX patterns."""


# ────────────────────────────────
# Language Detection Function
# ────────────────────────────────
def detect_language(text):
    tamil_chars = re.findall(r'[\u0B80-\u0BFF]', text)
    english_words = re.findall(r'[a-zA-Z]+', text)
    if len(tamil_chars) > len(english_words):
        return "tamil"
    elif len(english_words) > 0:
        return "english"
    else:
        return "english"


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
# UX-Optimized Text Processing (এগুলোও আগের মতোই)
# ────────────────────────────────
def split_sentences(text):
    abbrev = ['Dr.', 'Mr.', 'Mrs.', 'Ms.', 'Prof.', 'Sr.', 'Jr.', 'Md.', 'Adv.', 'Eng.', 'Capt.', 'Col.', 'Lt.', 'Maj.', 'Gen.']
    marker = '___ABBR___'
    for a in abbrev:
        text = text.replace(a, a.replace('.', marker))
    sentences = re.split(r'(?<=[.!?])\s+', text)
    clean = []
    for s in sentences:
        for a in abbrev:
            s = s.replace(a.replace('.', marker), a)
        clean.append(s)
    return clean




def remove_emojis_and_icons(text):
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        "]+", flags=re.UNICODE)
    text = emoji_pattern.sub('', text)
    symbols_to_remove = ['✨','💆','💇','💪','⏰','🌟','💡','📞','📅','💰','💯','🔥','💫','👑','✅','☑️','⚠️','❌']
    for symbol in symbols_to_remove:
        text = text.replace(symbol, '')
    return text.strip()


def detect_appointment_request(text):
    english_keywords = ['appointment', 'book', 'schedule', 'visit', 'consultation', 'meet', 'appoint', 'booking', 'reserve', 'arrange']
    tamil_keywords = ['அப্পায়্ন্ট্মেন্ট্', 'পুক্', 'সান্ধিপ্পু', 'ৱরুকৈ', 'নেরম্']
    text_lower = text.lower()
    return (any(keyword in text_lower for keyword in english_keywords) or
            any(keyword in text for keyword in tamil_keywords))


def apply_research_based_formatting(text, user_question):
    text = remove_emojis_and_icons(text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'*\1*', text)
    user_language = detect_language(user_question)
    sentences = split_sentences(text)
    formatted_paragraphs = []
    current_paragraph = []
    for sentence in sentences:
        current_paragraph.append(sentence)
        if len(current_paragraph) >= 2:
            formatted_paragraphs.append(' '.join(current_paragraph))
            current_paragraph = []
    if current_paragraph:
        formatted_paragraphs.append(' '.join(current_paragraph))
    text = '\n\n'.join(formatted_paragraphs)
    if detect_appointment_request(user_question):
        if user_language == "tamil":
            appointment_text = "\n\nअप्पাय়्न्ট्मেন्ট् পুক্ সেয়্য, তযৱুসেয়্তু এঙ্গळৈ +91 9003444435 ইল্ আযৈক্কৱুম্, এঙ্গळ् তোডর্বু কুযু ৱিরৈভিল্ উঙ্গळৈ তোডর্বু কোল্লুম্।"
        else:
            appointment_text = "\n\nTo book an appointment, please call us at +91 9003444435 and our contact team will get in touch with you shortly."
        if appointment_text not in text:
            text += appointment_text
    text = text.replace("dermijanofficialcontact@gmail.com", "*dermijanofficialcontact@gmail.com*")
    text = text.replace("+91 9003444435", "+91 9003444435")
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    return text.strip()


def clean_source_urls(text):
    text = re.sub(r'Sources?:.*$', '', text, flags=re.I|re.M)
    text = re.sub(r'Reference:.*$', '', text, flags=re.I|re.M)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'dermijan\.com\S*', '', text)
    return re.sub(r'\n\s*\n', '\n', text).strip()


# ────────────────────────────────
# ENHANCED Perplexity API Integration with Profile Support
# ────────────────────────────────
def get_perplexity_answer(question, uid):
    print(f"Question from {uid}: {question}")
    user_language = detect_language(question)
    print(f"Detected language: {user_language}")
    
    # Check if this is a greeting and if user has a profile
    is_greeting = detect_greeting_message(question)
    personalized_greeting = None
    
    if is_greeting:
        personalized_greeting = storage.generate_personalized_greeting(uid)
        print(f"Personalized greeting available: {bool(personalized_greeting)}")
    
    hist = mgr.get_history(uid)
    ctx = mgr.format_context(hist)
    
    # Add user profile context if available
    user_profile = storage.get_user_profile_summary(uid)
    profile_context = ""
    if user_profile['has_profile']:
        profile_context = f"\nUser Profile - Name: {user_profile['name'] or 'Not provided'}, "
        profile_context += f"Previous concerns: {', '.join([p['problem'] for p in user_profile['problems'][-3:]])}\n"
    
    if user_language == "tamil":
        language_instruction = "Respond ONLY in Tamil. Apply research-based formatting: short paragraphs (2-3 sentences), use hyphens (-) for bullets, *bold* for key info."
        not_found_msg = "That information isn't available in our approved sources. Please contact our support team for accurate details."
    else:
        language_instruction = "Respond ONLY in English. Apply research-based formatting: short paragraphs (2-3 sentences), use hyphens (-) for bullets, *bold* for key info."
        not_found_msg = "That information isn't available in our approved sources. Please contact our support team for accurate details."
    
    # Use personalized greeting if available and this is a greeting
    if is_greeting and personalized_greeting:
        print(f"✅ Using personalized greeting: {personalized_greeting}")
        mgr.store(uid, question, "user")
        mgr.store(uid, personalized_greeting, "bot")
        return personalized_greeting
    
    user_prompt = (
        f"Answer using ONLY information from these dermijan.com pages:\n"
        + "\n".join(ALLOWED_URLS) + "\n\n"
        + profile_context + ctx + f"User: {question}\n\n"
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
        "max_tokens": 800,
        "temperature": 0.2
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
            mgr.store(uid, question, "user")
            mgr.store(uid, formatted_reply, "bot")
            return formatted_reply
        else:
            print(f"Perplexity API error: {response.status_code} - {response.text}")
            return "Sorry, our service is temporarily unavailable.\n\nPlease try again later."
    except Exception as e:
        print(f"Perplexity exception: {e}")
        return "Sorry, there was a technical issue.\n\nPlease try again."


# ────────────────────────────────
# Universal Phone → WhatsApp chatId Function (No phonenumbers)
# ────────────────────────────────
def format_chatid(phone_number, default_country_code="880"):
    """
    Returns WhatsApp chatId as countrycode+number@c.us, eg: 8801xxxxxxxxx@c.us (Bangladesh), 9190xxxxxxxx@c.us (India)
    """
    number = str(phone_number).strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    if number.startswith('+'):
        number = number[1:]
    if number.startswith('00'):
        number = number[2:]
    if number.startswith('0'):
        number = default_country_code + number[1:]
    elif len(number) == 10 and number.isdigit():
        number = default_country_code + number
    return number + "@c.us"


# ────────────────────────────────
# WAHA Functions
# ────────────────────────────────
def extract_waha_messages(payload):
    messages = []
    try:
        print(f"🔍 WAHA webhook received: {json.dumps(payload, indent=2)}")
        if payload.get("event") == "message":
            data = payload.get("payload", {})
            sender = ""
            if "from" in data:
                sender = data["from"].replace("@c.us", "").replace("@s.whatsapp.net", "")
                if sender.startswith("880"):
                    sender = sender[3:]
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
    if not WAHA_BASE_URL:
        print("❌ WAHA Base URL missing")
        return False
    chat_id = format_chatid(to_phone, default_country_code="880") # বাংলাদেশ default, চাইলে "91"
    payload = {
        "session": WAHA_SESSION,
        "chatId": chat_id,
        "text": message
    }
    headers = {
        "Content-Type": "application/json",
        "x-api-key": WAHA_API_KEY
    }
    max_retries = 3
    retry_delay = [1, 2, 3]
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
    data = request.get_json()
    question = data.get("question")
    user_id = data.get("user_id", "anonymous")
    if not question:
        return jsonify({"reply": "Please provide a question."}), 400
    
    # Extract and save user data
    extraction_result = process_message_with_extraction(user_id, question)
    
    answer = get_perplexity_answer(question, user_id)
    
    return jsonify({
        "reply": answer,
        "extraction_result": extraction_result
    })


@app.route("/webhook", methods=["GET", "POST"])
def webhook_handler():
    if request.method == "GET":
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
            skip_phrases = ["sorry, our service", "মন্নিক্কবুম্", "dermijan.com",
                           "temporarily unavailable", "technical issue", "connection"]
            if any(phrase.lower() in text.lower() for phrase in skip_phrases):
                print("⏭️ Skipping bot message")
                continue
            
            # Extract and save user data
            print("🔍 Extracting user data...")
            extraction_result = process_message_with_extraction(sender, text)
            print(f"📊 Extraction result: {extraction_result}")
            
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
    history = mgr.get_history(user_id)
    return jsonify({"user_id": user_id, "conversation": history, "count": len(history)})


# NEW: User Profile Routes
@app.route("/user-profile/<phone>", methods=["GET"])
def get_user_profile(phone):
    """Get user profile including name and problems"""
    profile = storage.get_user_profile_summary(phone)
    return jsonify({
        "phone": phone,
        "profile": profile,
        "timestamp": datetime.now().isoformat()
    })


@app.route("/test-extraction", methods=["POST"])
def test_extraction():
    """Test name and problem extraction"""
    data = request.get_json()
    message = data.get("message", "")
    phone = data.get("phone", "test_user")
    
    if not message:
        return jsonify({"error": "Message required"}), 400
    
    # Test extraction
    extracted_name = extractor.extract_name(message)
    extracted_problems = extractor.extract_problems(message)
    
    # Test save (optional)
    if data.get("save", False):
        extraction_result = process_message_with_extraction(phone, message)
        return jsonify({
            "message": message,
            "extracted_name": extracted_name,
            "extracted_problems": extracted_problems,
            "save_result": extraction_result
        })
    
    return jsonify({
        "message": message,
        "extracted_name": extracted_name,
        "extracted_problems": extracted_problems,
        "save_executed": False
    })


@app.route("/waha-status", methods=["GET"])
def check_waha_status():
    try:
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
    try:
        redis_status = "connected" if redis_client.ping() else "disconnected"
    except:
        redis_status = "error"
    return jsonify({
        "status": "Dermijan Server Running - USER DATA EXTRACTION ENABLED",
        "version": "Enhanced with Complete Name & Problem Detection + Permanent Storage",
        "endpoints": ["/ask", "/webhook", "/conversation/<user_id>", "/user-profile/<phone>", 
                     "/test-extraction", "/waha-status", "/test-send", "/setup-waha-webhook"],
        "allowed_urls_count": len(ALLOWED_URLS),
        "redis_status": redis_status,
        "waha_config": {
            "base_url": WAHA_BASE_URL,
            "session": WAHA_SESSION,
            "send_endpoint": WAHA_SEND_TEXT_URL,
            "environment_controlled": True,
            "connection_retry": True
        },
        "new_features": {
            "user_name_extraction": True,
            "medical_problem_detection": True,
            "permanent_profile_storage": True,
            "personalized_greetings": True,
            "language_specific_extraction": ["English", "Tamil"],
            "conversation_vs_profile_storage": "7_days_vs_permanent",
            "complete_name_patterns": len(extractor.name_patterns['english']) + len(extractor.name_patterns['tamil']),
            "total_medical_problems": sum(len(lang['english']) + len(lang['tamil']) for lang in extractor.problem_keywords.values())
        },
        "extraction_capabilities": {
            "name_patterns_english": len(extractor.name_patterns['english']),
            "name_patterns_tamil": len(extractor.name_patterns['tamil']),
            "problem_categories": list(extractor.problem_keywords.keys()),
            "storage_method": "Redis permanent keys (no TTL)"
        },
        "data_structure": {
            "conversations": "whatsapp_chat:{phone} (7 days TTL)",
            "user_names": "user_profile:{phone}:name (permanent)",
            "user_problems": "user_profile:{phone}:problems (permanent)"
        },
        "ux_features": {
            "research_based_formatting": True,
            "mobile_optimized_paragraphs": True,
            "language_specific_responses": True,
            "readability_enhanced": True,
            "visual_hierarchy_implemented": True,
            "accessibility_compliant": True,
            "whatsapp_pattern_optimized": True,
            "scanning_friendly_layout": True,
            "personalized_user_experience": True
        }
    })


if __name__ == "__main__":
    print("🚀 Starting Dermijan Server - USER DATA EXTRACTION ENABLED")
    print(f"📋 Loaded {len(ALLOWED_URLS)} dermijan.com URLs")
    print("🎯 Features: Research-based formatting, Mobile-optimized, Visual hierarchy")
    print("✨ UX Enhancements: Short paragraphs, Strategic dots/hyphens, Scannable layout")
    print("📱 Mobile-first readability, Language-specific responses, Accessibility compliant")
    print(f"🔗 WAHA Integration: {WAHA_BASE_URL} (Session: {WAHA_SESSION})")
    print("⚙️ Environment Variables: WAHA_BASE_URL, WAHA_SESSION")
    print("💡 For localhost: Use ngrok to expose WAHA publicly")
    print("")
    print("🆕 NEW FEATURES:")
    print("   👤 Complete User Name Extraction (50+ patterns)")
    print("   🏥 186 Medical Problems Detection (English + Tamil)") 
    print("   💾 Dual Storage System: 7-day conversations + Permanent profiles")
    print("   🎭 Personalized Greetings based on User History")
    print("   🌐 Multi-language Extraction (English + Tamil)")
    print("   📊 Enhanced Analytics & User Profile Tracking")
    print(f"   📈 Total Name Patterns: {len(extractor.name_patterns['english']) + len(extractor.name_patterns['tamil'])}")
    print(f"   🔍 Total Medical Keywords: {sum(len(lang['english']) + len(lang['tamil']) for lang in extractor.problem_keywords.values())}")
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 8000)))
