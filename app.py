import os
from flask import Flask, render_template, request, jsonify
from services.yolo_service import detect_food
from services.gemini_service import get_nutrition_info
from services.ocr_service import OCRService

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Khởi tạo OCR Service ngay khi app chạy
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
            extracted_text = None # Mặc định là None
            
            if ocr_service:
                print("📖 Đang chạy OCR...")
                try:
                    # Gọi hàm extract_text từ service bạn vừa sửa
                    text_list = ocr_service.extract_text(filepath_fixed)
                    
                    if text_list and len(text_list) > 0:
                        # Nối list thành string (cách nhau bởi " | ")
                        extracted_text = " | ".join(text_list)
                        print(f"✅ OCR đọc được: {extracted_text}")
                    else:
                        print("⚠️ OCR không tìm thấy chữ nào.")
                except Exception as e:
                    print(f"❌ Lỗi khi chạy OCR: {e}")
                    # Không return lỗi, vẫn để app chạy tiếp chỉ với YOLO

            # ==========================================
            #  GEMINI 
            # ==========================================
            print("🤖 Đang gọi Gemini...")
            try:
                # Truyền cả tên món (YOLO) và chữ đọc được (OCR) vào
                menu_data = get_nutrition_info(detected_name, ocr_text=extracted_text)
            except Exception as e:
                print(f"❌ Lỗi Gemini: {e}")
                menu_data = {
                    "dish_name": detected_name,
                    "price": "Đang cập nhật",
                    "description": "Lỗi kết nối AI.",
                    "nutrition_summary": "Không thể lấy thông tin."
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