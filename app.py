import os
from flask import Flask, render_template, request, jsonify
from services.yolo_service import detect_food
from services.gemini_service import get_nutrition_info
from services.ocr_service import OCRService

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


try:
    ocr_service = OCRService()
    print("✅ OCR Service đã sẵn sàng!")
except Exception as e:
    print(f"❌ Lỗi khởi tạo OCR: {e}")
    ocr_service = None

@app.route('/health')
def health():
    return "OK", 200

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return jsonify({'error': 'Không có file ảnh'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Chưa chọn file'}), 400

    if file:
        try:
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            filepath_fixed = filepath.replace("\\", "/")

            target_language = request.form.get('language', 'English')
            print(f"🌐 Ngôn ngữ dịch: {target_language}")

            # ==========================================
            # YOLO DETECT 
            # ==========================================
            print(f"🔍 Đang chạy YOLO cho ảnh: {filename}")
            detected_name = detect_food(filepath_fixed)
            
            if not detected_name:
                return jsonify({
                    'success': False, 
                    'message': 'Không nhận diện được món ăn nào.'
                })
            
            print(f"✅ YOLO phát hiện: {detected_name}")

            # ==========================================
            #  OCR 
            # ==========================================
            extracted_text = None 
            
            if ocr_service:
                print("📖 Đang chạy OCR...")
                try:
                 
                    text_list = ocr_service.extract_text(filepath_fixed)
                    
                    if text_list and len(text_list) > 0:
                     
                        extracted_text = " | ".join(text_list)
                        print(f"✅ OCR đọc được: {extracted_text}")
                    else:
                        print("⚠️ OCR không tìm thấy chữ nào.")
                except Exception as e:
                    print(f"❌ Lỗi khi chạy OCR: {e}")
                    

            # ==========================================
            #  GEMINI 
            # ==========================================
            print("🤖 Đang gọi Gemini...")
            try:
            
                menu_data = get_nutrition_info(detected_name, ocr_text=extracted_text, target_language=target_language)
            except Exception as e:
                print(f"❌ Lỗi Gemini: {e}")
                menu_data = {
                    "dish_name": detected_name,
                    "price": "Unavailable",
                    "description": "Connection error.",
                    "nutrition_summary": "Cannot fetch data.",
                    "tags": []
                }

          
            return jsonify({
                'success': True,
                'image_url': f"/{filepath_fixed}", 
                'data': menu_data,
                'debug_ocr': extracted_text 
            })

        except Exception as e:
            print(f"❌ Lỗi Server: {e}") 
            return jsonify({'error': f'Lỗi server nội bộ: {str(e)}'}), 500

if __name__ == '__main__':
   
    app.run(debug=True, port=5000)