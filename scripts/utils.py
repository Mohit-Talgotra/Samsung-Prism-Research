import base64
from io import BytesIO
import requests
from dotenv import load_dotenv
import os

def call_ollama(model, prompt, images):
    load_dotenv()
    url = os.getenv("OLLAMA_LOCAL_URL") + "/api/generate"
    
    payload = {
        "model": model,
        "prompt": prompt,
        "images": images,
        "stream": False
    }
    
    response = requests.post(url, json=payload)
    return response.json()

def encode_image(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    encoded_string = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return encoded_string

def build_gemini_payload(prompt, base64_images, model):
    parts = []

    parts.append({
        "text": prompt
    })

    for base64_img in base64_images:
        parts.append({
            "inline_data": {
                "mime_type": "image/png",
                "data": base64_img
            }
        })

    return {
        "contents": [{
            "parts": parts
        }],
        "generationConfig": {
            "temperature": 0.1,
            "topP": 0.001,
            "maxOutputTokens": 512
        }
    }

def call_gemini_api(api_key, payload):
    api = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={api_key}"

    headers = {
        "Content-Type": "application/json",
    }

    response = requests.post(api, headers=headers, json=payload)
    return response.json()