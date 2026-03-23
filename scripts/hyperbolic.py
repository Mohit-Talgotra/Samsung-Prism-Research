
import base64
import requests
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
import os

def encode_image(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    encoded_string = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return encoded_string

def build_payload(prompt, base64_img, model):
    return {
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"},
                },
            ],
        }],
        "model": model,
        "max_tokens": 512,
        "temperature": 0.1,
        "top_p": 0.001,
    }

def call_hyperbolic_api(api_key, payload):
    api = "https://api.hyperbolic.xyz/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    response = requests.post(api, headers=headers, json=payload)
    return response.json()

def main():
    load_dotenv()
    
    api_key = os.getenv("HYPERBOLIC_API_KEY")
    
    img_path = r"C:\Users\YASHWANTH\Pictures\Screenshots\Screenshot 2025-09-03 090908.png"
    img = Image.open(img_path)
    base64_img = encode_image(img)
    
    prompt = "What is in this image?"
    model = "Qwen/Qwen2.5-VL-7B-Instruct"
    payload = build_payload(prompt, base64_img, model)
    
    result = call_hyperbolic_api(api_key, payload)
    
    print(result["choices"][0]["message"]["content"])

if __name__ == "__main__":
    main()
