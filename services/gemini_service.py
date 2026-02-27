import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

client = None
if API_KEY:
    client = genai.Client(api_key=API_KEY)


def get_nutrition_info(food_name, ocr_text=None):
    if not client:
        return {"error": "Chưa cấu hình API Key"}
    
    print(f" Gemini đang viết mô tả cho món: {food_name}...")

   
    ocr_context = ""

    if ocr_text:
        ocr_context = f"""
        Additional information from OCR (text read from the image): "{ocr_text}".
        Please use this information to:
        1. Determine a more accurate dish name (e.g., if the identified dish is "Pho", but OCR reads "Special Pho", use "Special Pho").
        2. Find the exact price associated with the dish "{food_name}".
        """
        
    prompt = f"""
    The identified dish is: "{food_name}".
    {ocr_context}
    
    Act as a culinary expert writing content for a restaurant menu.
    Your tasks:
    1. Provide the dish name in English (translate from Vietnamese if necessary).
    2. Write an appetizing description.
    3. Write a brief nutrition summary.
    4. Find the price from the provided text. If no price is available, output "Unavailable".
    5. Normalize the price into a numeric format (e.g., "35k" -> 35000, "35.000" -> 35000).

    Return a JSON object with the exact following structure. All text values MUST be in English:
    {{
        "dish_name": "Dish name in English",
        "price": "Unavailable (or the numeric price found)",
        "description": "A short, appetizing description of about 2-3 sentences in English.",
        "nutrition_summary": "A brief summary of calories, protein, and health benefits in English."
    }}
    """
    
    response_schema = {
        "type": "OBJECT",
        "properties": {
            "dish_name": {"type": "STRING"},
            "price": {"type": "STRING"},
            "description": {"type": "STRING"},
            "nutrition_summary": {"type": "STRING"}
        },
        "required": ["dish_name", "price", "description", "nutrition_summary"]
    }
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema
            )
        )
        data = json.loads(response.text)
        return data

    except Exception as e:
        print(f"❌ Lỗi Gemini: {e}")
        return {
            "dish_name": food_name,
            "price": "Unavailable",
            "description": "Không thể lấy mô tả.",
            "nutrition_summary": "Không thể phân tích dinh dưỡng."
        }

