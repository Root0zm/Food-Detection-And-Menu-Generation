#yolo
import os
import cv2
from ultralytics import YOLO

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'best.pt')


try:
    print(f"🔄 Đang load model từ: {MODEL_PATH}")
    model = YOLO(MODEL_PATH)
except Exception as e:
    print(f"Lỗi load model: {e}")
    model = None

def detect_food(image_path, is_menu=False):
    if model is None:
        return []

    filename = os.path.basename(image_path)
    
    # Increase image size for menu to detect smaller dishes in a large image
    img_size = 1920 if is_menu else 640
    # Lower confidence slightly for menu to catch more dishes
    confidence_thresh = 0.15 if is_menu else 0.25

    # save=True: save img with box
    # project/name: img path
    results = model.predict(
        image_path, 
        conf=confidence_thresh, 
        iou=0.45,
        imgsz=img_size,
        save=True, 
        project=os.path.join(BASE_DIR, 'static'),
        name='debug', 
        exist_ok=True 
    )
    
    detected_items = []
    
    for result in results:
        if len(result.boxes) == 0:
            print("Không thấy món nào!")
            continue

        for box in result.boxes:
            class_id = int(box.cls[0].item())
            class_name = result.names[class_id]
            confidence = float(box.conf[0].item())
            
            # get bounding box: [x1, y1, x2, y2]
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            
            print(f"   👉 Server thấy: {class_name} ({confidence:.2f})")

            detected_items.append({
                'class_name': class_name,
                'confidence': confidence,
                'box': [x1, y1, x2, y2]
            })
            
    print(f"Kết quả chốt: {len(detected_items)} món")
    return detected_items