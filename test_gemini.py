# test_gemini.py
import os
import requests

# 1) Read your key from the environment
key = os.getenv("GEMINI_API_KEY")
if not key:
    raise RuntimeError("GEMINI_API_KEY not set in environment")

# 2) Build the URL and payload
url = (
    "https://generativelanguage.googleapis.com/v1beta/"
    f"models/gemini-2.0-flash:generateContent?key={key}"
)
payload = {
    "contents": [
        { "parts": [{ "text": "Hello, how are you?" }] }
    ]
}

# 3) Send the request and print the response
resp = requests.post(url, json=payload)
print("Status code:", resp.status_code)
print("Response body:", resp.text)
