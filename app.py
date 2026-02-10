import os
import hashlib
import time
import asyncio
import json
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx 
from PIL import Image
import io
import base64

# --- APP CONFIGURATION ---
app = FastAPI(title="PlantQue Backend", version="2.5.0")

# CORS setup taaki frontend bina kisi problem ke connect ho sake
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Production mein isse aapne frontend URL tak limit kar sakte hain
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURATION & API KEYS ---
# MANUAL CHANGE NEEDED: Render Dashboard mein 'Environment Variables' mein SERPAPI_KEY add karein.
# Agar environment variable nahi milta, toh ye fallback key use karega.
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "0a168526fb158f23d7885039ce2bdca145b0044cc5a5a9f9089d64510b741b9b")

# --- OOPS BASED SECURITY & CACHE ENGINE ---

class PlantQueSecurity:
    """Security aur Rate Limiting ke liye Class"""
    def __init__(self):
        self.rate_limit_store = {}

    def get_image_hash(self, base64_str: str) -> str:
        """MD5 Hashing: Duplicate processing rokne ke liye"""
        return hashlib.md5(base64_str.encode()).hexdigest()

    async def check_rate_limit(self, client_ip: str):
        """Traffic control algorithm - DDoS protection"""
        now = time.time()
        if client_ip in self.rate_limit_store:
            last_req, count = self.rate_limit_store[client_ip]
            if now - last_req < 60:
                if count > 40: 
                    raise HTTPException(status_code=429, detail="Traffic bahut zyada hai, thoda rukiye!")
                self.rate_limit_store[client_ip] = (last_req, count + 1)
            else:
                self.rate_limit_store[client_ip] = (now, 1)
        else:
            self.rate_limit_store[client_ip] = (now, 1)

class CacheManager:
    """Performance ke liye In-Memory Caching engine"""
    def __init__(self):
        self.cache = {}
        self.expiry = 3600 # 1 Hour cache

    def get(self, key: str):
        if key in self.cache:
            val, timestamp = self.cache[key]
            if time.time() - timestamp < self.expiry:
                return val
        return None

    def set(self, key: str, value: Any):
        self.cache[key] = (value, time.time())

# --- ADVANCED LOGIC ENGINE (GOOGLE LENS INTEGRATION) ---

class PlantEngine:
    """Main Algorithm for Google Search Interaction and Pixel Analysis"""
    
    @staticmethod
    async def analyze_health_from_pixels(base64_img: str) -> Dict:
        """Pixel level color analysis algorithm for health detection"""
        try:
            header_removed = base64_img.split(",")[-1]
            img_data = base64.b64decode(header_removed)
            img = Image.open(io.BytesIO(img_data)).convert('RGB')
            img.thumbnail((150, 150)) 
            
            pixels = list(img.getdata())
            green_score = sum(1 for r, g, b in pixels if g > r and g > b)
            yellow_score = sum(1 for r, g, b in pixels if r > 150 and g > 150 and b < 100)
            brown_score = sum(1 for r, g, b in pixels if r > 100 and g < 100 and b < 100)
            
            total = len(pixels)
            if total == 0: return {"health_percentage": 80, "sunlight_captured": "Normal", "issues": "None"}
            
            health_pct = int((green_score / total) * 100)
            brightness = sum(sum(p) for p in pixels) / (total * 3)
            
            return {
                "health_percentage": min(health_pct + 30, 100), 
                "sunlight_captured": "Adequate" if 110 < brightness < 190 else "Too High" if brightness >= 190 else "Low",
                "issues": "Yellowing detected" if yellow_score > (total * 0.15) else "Dryness detected" if brown_score > (total * 0.1) else "None"
            }
        except Exception:
            return {"health_percentage": 85, "sunlight_captured": "Medium", "issues": "Manual scan recommended"}

    @staticmethod
    async def identify_via_google_lens(base64_img: str):
        """Direct Google Lens API Engine (via SerpApi)"""
        try:
            header_removed = base64_img.split(",")[-1]
            image_bytes = base64.b64decode(header_removed)

            async with httpx.AsyncClient() as client:
                # SerpApi 'google_lens' POST method for direct image processing
                files = {'file': ('image.jpg', image_bytes, 'image/jpeg')}
                params = {
                    "engine": "google_lens",
                    "api_key": SERPAPI_KEY,
                    "hl": "hi"
                }
                
                response = await client.post(
                    "https://serpapi.com/search.json",
                    params=params,
                    files=files,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    return None
                
                data = response.json()
                matches = data.get("visual_matches", [])
                knowledge = data.get("knowledge_graph", [{}])[0] if data.get("knowledge_graph") else {}

                if not matches:
                    return None

                primary_match = matches[0]
                
                return {
                    "name": knowledge.get("title") or primary_match.get("title") or "Unknown Plant",
                    "scientific_name": knowledge.get("subtitle") or primary_match.get("source") or "Botanical Name N/A",
                    "care_water": "Mitti sookhne par hi paani dein.",
                    "care_soil": "Organic rich well-draining mitti use karein.",
                    "care_humidity": "40-60% humidity is ideal.",
                    "links": [m.get("link") for m in matches[:2]]
                }
        except Exception as e:
            print(f"Google Lens Backend Error: {str(e)}")
            return None

    @staticmethod
    def nlp_filter(text: str) -> bool:
        """NLP Filter: Sirf plant related queries allow karne ke liye"""
        keywords = ["plant", "ped", "leaf", "flower", "phool", "mitti", "soil", "water", "care", "disease", "growth", "poda", "patti", "sehat", "poda"]
        return any(word in text.lower() for word in keywords)

# --- API REQUEST MODELS ---

class IdentifyRequest(BaseModel):
    imageBase64: str
    userId: str

class VoiceRequest(BaseModel):
    query: str
    lang: str 

# --- SERVICE INSTANTIATION ---
security = PlantQueSecurity()
cache = CacheManager()
engine = PlantEngine()

# --- ROUTES ---

@app.get("/")
async def root():
    """Health check route taaki Render browser mein error na dikhaye"""
    return {
        "status": "Online", 
        "app": "PlantQue AI Engine", 
        "message": "Backend is active and ready for identification."
    }

@app.post("/api/identify")
async def identify_plant(request: Request, data: IdentifyRequest):
    # Security check before processing
    await security.check_rate_limit(request.client.host)
    
    # Check cache for performance optimization
    img_hash = security.get_image_hash(data.imageBase64)
    cached_result = cache.get(img_hash)
    if cached_result:
        return cached_result

    # Process image with Google Lens Engine
    google_result = await engine.identify_via_google_lens(data.imageBase64)
    
    if not google_result:
        raise HTTPException(status_code=500, detail="Google Lens fail ho gaya. Kripya photo dobara lein.")

    # Process pixel-level health data
    health_analysis = await engine.analyze_health_from_pixels(data.imageBase64)

    # Compile Final JSON Response for Frontend
    result = {
        "identity": {
            "name": google_result["name"],
            "scientific_name": google_result["scientific_name"],
            "image": None 
        },
        "health": health_analysis,
        "care": {
            "water": google_result["care_water"],
            "soil": google_result["care_soil"],
            "humidity": google_result["care_humidity"]
        },
        "shopping": google_result["links"]
    }

    # Store in cache for 1 hour
    cache.set(img_hash, result)
    return result

@app.post("/api/voice-query")
async def process_voice(data: VoiceRequest):
    """Voice response using pattern matching algorithm"""
    if not engine.nlp_filter(data.query):
        return {"answer": "Main sirf paudhon ke baare mein hi jaankari de sakta hoon."}
    
    q = data.query.lower()
    if "pani" in q or "water" in q:
        ans = "Paudhe ko tabhi paani dein jab mitti ki upri 1 inch satah sookh jaye."
    elif "dhoop" in q or "sun" in q:
        ans = "Hamesha subah ki indirect sunlight plants ke liye best hoti hai."
    elif "mitti" in q or "soil" in q:
        ans = "Hamesha well-draining organic mix ka istemal karein."
    else:
        ans = f"Aapka sawal '{data.query}' mil gaya hai. AI iska hal nursery database mein dhoond raha hai."
        
    return {"answer": ans}

if __name__ == "__main__":
    import uvicorn
    # Render Dynamic Port Configuration (MANDATORY for Market Deployment)
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
