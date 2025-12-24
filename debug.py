import os
from flask import Flask, render_template, request, jsonify
from services.yolo_service import detect_food
from services.gemini_service import get_nutrition_info

app = Flask(__name__)

# Cấu hình thư mục lưu ảnh
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    # 1. Kiểm tra file gửi lên
    if 'file' not in request.files:
        return jsonify({'error': 'Không có file ảnh'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Chưa chọn file'}), 400

    if file:
        try:
            # 2. Lưu ảnh
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)

            # 3. Gọi YOLO
            detected_name = detect_food(filepath)
            
            if not detected_name:
                return jsonify({
                    'success': False, 
                    'message': 'Không nhận diện được món ăn.'
                })
            
            # 4. Chuẩn bị OCR (Tương lai)
            extracted_text = None 

            # 5. Gọi Gemini
            try:
                menu_data = get_nutrition_info(detected_name, ocr_text=extracted_text)
            except Exception:
                # Nếu Gemini lỗi thì trả về dữ liệu mặc định để web không chết
                menu_data = {
                    "dish_name": detected_name,
                    "price": "Đang cập nhật",
                    "description": "Không thể lấy mô tả lúc này.",
                    "nutrition_summary": "Không thể lấy thông tin dinh dưỡng."
                }

            # 6. Trả kết quả về Frontend
            return jsonify({
                'success': True,
                'image_url': f"/{filepath}",
                'data': menu_data
            })

        except Exception as e:
            # Nếu lỗi hệ thống, trả về mã 500
            return jsonify({'error': 'Lỗi server nội bộ.'}), 500

if __name__ == '__main__':
    # Lưu ý: debug=True giúp tự động reload khi sửa code. 
    # Khi nào nộp bài hoặc chạy thật thì sửa thành debug=False.
    app.run(debug=True, port=5000)