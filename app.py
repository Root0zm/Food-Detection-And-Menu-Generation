import os
from flask import Flask, render_template, request, jsonify
from services.yolo_service import detect_food
from services.gemini_service import get_nutrition_info

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return jsonify({'error': 'Không có file ảnh được gửi lên'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Chưa chọn file'}), 400

    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        detected_name = detect_food(filepath)

        if not detected_name:
            return jsonify({
                'success': False,
                'message': 'Không nhận diện được món ăn nào trong ảnh.'
            })
        ##extracted_text = None 
        menu_data = get_nutrition_info(detected_name, ocr_text=extracted_text)
        return jsonify({
            'success': True,
            'image_url': f"/{filepath}",
            'data': menu_data
        })
if __name__ == '__main__':
    app.run(debug=True, port=5000)