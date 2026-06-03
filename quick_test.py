"""Quick test to see if Gemini API is responding."""
import google.generativeai as genai
import time
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"Testing with API key: {api_key[:20]}...")

genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-3.1-flash-lite')

print("\n⏱️ Testing API response time...")
print("Sending a simple prompt...\n")

start_time = time.time()

try:
    response = model.generate_content("Say 'Hello! API is fast and working!'")
    end_time = time.time()
    
    print(f"✅ Response received in {end_time - start_time:.2f} seconds")
    print(f"Response: {response.text}\n")
    
    # Now test with a longer prompt (like resume analysis)
    print("Testing with a longer prompt (simulating resume analysis)...")
    start_time = time.time()
    
    long_prompt = """
    Analyze this candidate profile and provide scores:
    
    Name: John Doe
    Experience: 5 years of Python development
    Projects: Built 3 web applications using Django and React
    GitHub: 50+ contributions to open source projects
    Skills: Python, JavaScript, React, Django, PostgreSQL
    
    Provide scores for:
    1. Open Source contributions (max 35)
    2. Self Projects (max 30)
    3. Production experience (max 25)
    4. Technical skills (max 10)
    """
    
    response = model.generate_content(long_prompt)
    end_time = time.time()
    
    print(f"✅ Long response received in {end_time - start_time:.2f} seconds")
    print(f"Response length: {len(response.text)} characters\n")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
