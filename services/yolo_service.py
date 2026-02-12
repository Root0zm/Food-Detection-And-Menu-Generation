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

def detect_food(image_path):
    if model is None:
        return None

    filename = os.path.basename(image_path)
    
    # save=True: save img with box
    # project/name: img path
    # conf=0.25: confidence threshold
    results = model.predict(
        image_path, 
        conf=0.25, 
        save=True, 
        project=os.path.join(BASE_DIR, 'static'),
        name='debug', 
        exist_ok=True 
    )
    
    best_class = None
    max_conf = -1
    
    for result in results:


        if len(result.boxes) == 0:
            print("Không thấy món nào!")
            return None

        for box in result.boxes:
            class_id = int(box.cls[0].item())
            class_name = result.names[class_id]
            confidence = float(box.conf[0].item())
            
            print(f"   👉 Server thấy: {class_name} ({confidence:.2f})")

            if confidence > max_conf:
                max_conf = confidence
                best_class = class_name
            
    print(f"Kết quả chốt: {best_class}")
    
    return best_class