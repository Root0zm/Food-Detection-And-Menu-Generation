import os
import sys

# Khống chế OpenMP và MKL threads để tránh deadlock khi chạy PaddleOCR trong Flask thread
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["FLAGS_use_onednn"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "0"

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
    print(" OCR Service đã sẵn sàng!")
except Exception as e:
    print(f" Lỗi khởi tạo OCR: {e}")
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
            mode = request.form.get('mode', 'scan')
            print(f" Ngôn ngữ: {target_language}, Chế độ: {mode}")

            # ==========================================
            # YOLO DETECT 
            # ==========================================
            print(f"Đang chạy YOLO: {filename}")
            detected_items = detect_food(filepath_fixed, is_menu=(mode == 'menu'))
            
            if not detected_items:
                return jsonify({
                    'success': False, 
                    'message': 'Không nhận diện được món ăn nào.'
                })
                
            # ==========================================
            #  OCR 
            # ==========================================
            ocr_items = []
            if ocr_service:
                print(" Đang chạy OCR...")
                try:
                    ocr_items = ocr_service.extract_text(filepath_fixed)
                except Exception as e:
                    print(f" Lỗi khi chạy OCR: {e}")

            # Helper functions for centroid calculation
            def get_centroid_box(box):
                return ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
                
            def get_centroid_poly(poly):
                xs = [p[0] for p in poly]
                ys = [p[1] for p in poly]
                return (sum(xs) / len(xs), sum(ys) / len(ys))

            import math

            if mode == 'scan':
                # Pick the one with max confidence
                best_item = max(detected_items, key=lambda x: x['confidence'])
                detected_name = best_item['class_name']
                
                print(f" YOLO phát hiện tốt nhất: {detected_name}")
                
                extracted_text = None
                if ocr_items:
                    text_list = [item['text'] for item in ocr_items]
                    extracted_text = " | ".join(text_list)
                    print(f" OCR đọc được: {extracted_text}")
                
                print("Đang gọi Gemini...")
                try:
                    menu_data = get_nutrition_info(detected_name, ocr_text=extracted_text, target_language=target_language)
                except Exception as e:
                    print(f" Lỗi Gemini: {e}")
                    menu_data = {"dish_name": detected_name, "price": "Unavailable", "description": "Connection error.", "nutrition_summary": "Cannot fetch data.", "tags": []}

                return jsonify({
                    'success': True,
                    'image_url': f"/{filepath_fixed}", 
                    'data': menu_data,
                    'debug_ocr': extracted_text 
                })

            elif mode == 'menu':
                import uuid
                from PIL import Image
                import copy
                
                results_items = []
                original_img = Image.open(filepath_fixed)
                gemini_cache = {}  # Cache to reuse Gemini results
                
                for i, item in enumerate(detected_items):
                    c_i = item['class_name']
                    s_i = item['confidence']
                    b_i = item['box']
                    
                    # 1. Spatial Association (Associate name + price)
                    t_i_star = "Unavailable"
                    if ocr_items:
                        w_img, h_img = original_img.size
                        norm_scale = 800.0 / float(max(w_img, h_img))
                        dist_threshold = 140.0
                        
                        b_norm = [x * norm_scale for x in b_i]
                        
                        ocr_with_dist = []
                        for ocr_item in ocr_items:
                            poly_norm = [[pt[0] * norm_scale, pt[1] * norm_scale] for pt in ocr_item['box']]
                            ox, oy = get_centroid_poly(poly_norm)
                            
                            # Closest point on food boundary in normalized space
                            cx = max(b_norm[0], min(ox, b_norm[2]))
                            cy = max(b_norm[1], min(oy, b_norm[3]))
                            
                            dx = ox - cx
                            dy = oy - cy
                            
                            # Penalize elements that are above the food box
                            if oy < b_norm[1]:
                                dy = dy * 5.0
                                
                            edge_dist = math.hypot(dx, dy)
                            ocr_with_dist.append((edge_dist, ocr_item))
                            
                        ocr_with_dist.sort(key=lambda x: x[0])
                        
                        # Gather all ocr_items within the distance threshold (cap at top 3 to prevent spillover)
                        associated_texts = []
                        for dist, ocr_item in ocr_with_dist:
                            if dist <= dist_threshold:
                                associated_texts.append(ocr_item)
                            if len(associated_texts) >= 3:
                                break
                                
                        # Sort associated OCR items by reading order (top-to-bottom, then left-to-right)
                        if associated_texts:
                            associated_texts_with_centroid = []
                            for a_item in associated_texts:
                                cy = get_centroid_poly(a_item['box'])[1]
                                cx = get_centroid_poly(a_item['box'])[0]
                                associated_texts_with_centroid.append((cy, cx, a_item))
                                
                            associated_texts_with_centroid.sort(key=lambda x: x[0])
                            
                            # Group into rows with tolerance adjusted to image size
                            rows = []
                            current_row = []
                            current_y = -1
                            row_tolerance = max(15.0, 20.0 * norm_scale)
                            
                            for cy, cx, a_item in associated_texts_with_centroid:
                                if current_y == -1:
                                    current_y = cy
                                    current_row.append((cx, a_item))
                                elif abs(cy - current_y) < row_tolerance:
                                    current_row.append((cx, a_item))
                                else:
                                    current_row.sort(key=lambda x: x[0])
                                    rows.append(current_row)
                                    current_y = cy
                                    current_row = [(cx, a_item)]
                            if current_row:
                                current_row.sort(key=lambda x: x[0])
                                rows.append(current_row)
                                
                            # Flatten rows
                            final_sorted_texts = []
                            for row in rows:
                                row_str = " ".join([x[1]['text'] for x in row])
                                final_sorted_texts.append(row_str)
                                
                            t_i_star = " | ".join(final_sorted_texts)
                            
                    print(f" Món: {c_i}, Độ tin cậy: {s_i:.2f}, Chữ liên kết: {t_i_star}")
                    
                    # 2. Crop Image
                    crop_filename = f"crop_{uuid.uuid4().hex[:8]}.jpg"
                    crop_filepath = os.path.join(app.config['UPLOAD_FOLDER'], crop_filename)
                    # Expand box slightly
                    x1, y1, x2, y2 = b_i
                    cropped_img = original_img.crop((x1, y1, x2, y2))
                    # Convert RGBA to RGB if needed (JPEG doesn't support transparency)
                    if cropped_img.mode == 'RGBA':
                        cropped_img = cropped_img.convert('RGB')
                    cropped_img.save(crop_filepath)
                    crop_filepath_fixed = crop_filepath.replace("\\", "/")
                    
                    # 3. Call Gemini or Use Cache
                    cache_key = c_i
                    if cache_key in gemini_cache:
                        print(f" Dùng lại kết quả Gemini cho món: {c_i}")
                        menu_data = copy.deepcopy(gemini_cache[cache_key])
                       
                    else:
                        try:
                            menu_data = get_nutrition_info(c_i, ocr_text=t_i_star, target_language=target_language)
                            gemini_cache[cache_key] = copy.deepcopy(menu_data)
                        except Exception as e:
                            print(f" Lỗi Gemini: {e}")
                            menu_data = {"dish_name": c_i, "price": "Unavailable", "description": "Connection error.", "nutrition_summary": "Cannot fetch data.", "tags": []}
                    
                    results_items.append({
                        'image_url': f"/{crop_filepath_fixed}",
                        'data': menu_data,
                        'debug_ocr': t_i_star
                    })
                    
                return jsonify({
                    'success': True,
                    'items': results_items
                })

        except Exception as e:
            print(f"Lỗi Server: {e}") 
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'Lỗi server nội bộ: {str(e)}'}), 500

if __name__ == '__main__':
   
    app.run(debug=True, port=5000)