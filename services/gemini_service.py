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

# WIP
def get_nutrition_info(food_name, ocr_text=None):
    if not client:
        return {"error": "Chưa cấu hình API Key"}
    
    print(f" Gemini đang viết mô tả cho món: {food_name}...")

    # WIP
    ocr_context = ""
    if ocr_text:
       if ocr_text:
        # Sửa lại câu dẫn dắt một chút để AI hiểu ngữ cảnh hơn
        ocr_context = f"""
        Thông tin bổ sung từ OCR (chữ đọc được trên ảnh): "{ocr_text}".
        Hãy sử dụng thông tin này để:
        1. Xác định tên món chính xác hơn (ví dụ YOLO ra "Phở", nhưng OCR ra "Phở Đặc Biệt" thì dùng "Phở Đặc Biệt").
        2. Tìm chính xác giá tiền gắn liền với món "{food_name}".
        """
    # PROMPT can be change for other use
    prompt = f"""
    Món ăn được nhận diện là: "{food_name}".
    {ocr_context}
    
    Hãy đóng vai một chuyên gia ẩm thực viết nội dung cho menu nhà hàng.
    Nhiệm vụ:
    1. Dịch tên món sang Tiếng Việt (hoặc Tiếng Anh nếu phổ biến).
    2. Viết mô tả hấp dẫn (Description).
    3. Viết tóm tắt dinh dưỡng (Estimated nutrition).
    4. Tìm giá tiền (Price). Nếu trong thông tin tôi cung cấp không có giá, hãy để là "Unavailable".
    5. Chuẩn hóa giá tiền về dạng số (Ví dụ: "35k" -> 35000, "35.000" -> 35000).

    Trả về JSON với cấu trúc chính xác như sau:
    {{
        "dish_name": "Tên món",
        "price": "Unavailable (hoặc giá tìm được từ text)",
        "description": "Đoạn mô tả ngắn gọn, hấp dẫn khoảng 2-3 câu.",
        "nutrition_summary": "Tóm tắt ngắn gọn về calo, protein và lợi ích sức khỏe."
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

