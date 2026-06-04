#yolo
import os
import sys
import site
import cv2
import numpy as np

# Windows DLL loading resolution for NVIDIA CUDA libraries in virtual environment site-packages
if sys.platform == 'win32':
    try:
        for sp in site.getsitepackages():
            nvidia_dir = os.path.join(sp, 'nvidia')
            if os.path.exists(nvidia_dir):
                for root, dirs, files in os.walk(nvidia_dir):
                    if root.endswith('bin'):
                        try:
                            os.add_dll_directory(root)
                        except Exception:
                            pass
    except Exception:
        pass

from ultralytics import YOLO

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'best.pt')


try:
    import torch
    device_status = "GPU/CUDA" if torch.cuda.is_available() else "CPU"
    print(f"🔄 Đang load model từ: {MODEL_PATH} ({device_status})")
    model = YOLO(MODEL_PATH)
except Exception as e:
    print(f"Lỗi load model: {e}")
    model = None

def compute_iou(box1, box2):
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    inter_area = max(0, x2 - x1) * max(0, y2 - y1)
    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])

    iou = inter_area / float(box1_area + box2_area - inter_area + 1e-6)
    return iou

def detect_food(image_path, is_menu=False):
    if model is None:
        return []

    filename = os.path.basename(image_path)
    
    if not is_menu:
        # Standard detection for Scan Food
        results = model.predict(
            image_path, 
            conf=0.25, 
            iou=0.45,
            imgsz=640,
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
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                print(f"  {class_name} ({confidence:.2f})")
                detected_items.append({
                    'class_name': class_name,
                    'confidence': confidence,
                    'box': [x1, y1, x2, y2]
                })
        print(f"Kết quả chốt: {len(detected_items)} món")
        return detected_items

    # --- SAHI / Sliding Window Inference for Menu ---
   
    img = cv2.imread(image_path)
    if img is None:
        return []
        
    h, w, _ = img.shape
    patches = []
    
    # 1. Full image (resize slightly for speed, e.g. 1280)
    patches.append({'img': img, 'offset_x': 0, 'offset_y': 0, 'imgsz': 1280})
    
    # 2. Slice into 3x3 grid with 25% overlap
    grid_size = 3
    step_x = w // grid_size
    step_y = h // grid_size
    overlap_x = int(step_x * 0.25)
    overlap_y = int(step_y * 0.25)
    
    for i in range(grid_size):
        for j in range(grid_size):
            x1 = j * step_x - (overlap_x if j > 0 else 0)
            y1 = i * step_y - (overlap_y if i > 0 else 0)
            x2 = (j + 1) * step_x + (overlap_x if j < grid_size - 1 else 0)
            y2 = (i + 1) * step_y + (overlap_y if i < grid_size - 1 else 0)
            
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(w, x2)
            y2 = min(h, y2)
            
            patch_img = img[y1:y2, x1:x2]
            patches.append({'img': patch_img, 'offset_x': x1, 'offset_y': y1, 'imgsz': 640})

    all_detections = []
    
    for idx, patch in enumerate(patches):
        # We don't save patch images to avoid cluttering debug folder
        results = model.predict(
            patch['img'], 
            conf=0.15, 
            iou=0.45,
            imgsz=patch['imgsz'],  
            verbose=False
        )
        
        for result in results:
            if len(result.boxes) == 0: continue
            for box in result.boxes:
                class_id = int(box.cls[0].item())
                class_name = result.names[class_id]
                confidence = float(box.conf[0].item())
                
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                
                # Map coordinates back to original image
                orig_x1 = x1 + patch['offset_x']
                orig_y1 = y1 + patch['offset_y']
                orig_x2 = x2 + patch['offset_x']
                orig_y2 = y2 + patch['offset_y']
                
                all_detections.append({
                    'class_name': class_name,
                    'confidence': confidence,
                    'box': [orig_x1, orig_y1, orig_x2, orig_y2]
                })

    # Apply Class-specific Custom NMS
    all_detections.sort(key=lambda x: x['confidence'], reverse=True)
    final_items = []
    
    for item in all_detections:
        # Ignore detections below final confidence threshold
        if item['confidence'] < 0.25:
            continue
            
        keep = True
        for final_item in final_items:
            iou_val = compute_iou(item['box'], final_item['box'])
            if item['class_name'] == final_item['class_name']:
                # Same class: suppress if overlap is significant
                if iou_val > 0.35:
                    keep = False
                    break
            else:
                # Different classes: only suppress if they are almost completely overlapping
                # (prevents double-detection of the exact same dish under different labels)
                if iou_val > 0.80:
                    keep = False
                    break
        if keep:
            final_items.append(item)
            print(f"    {item['class_name']} ({item['confidence']:.2f})")
            
    print(f"Kết quả : {len(final_items)} món")
    return final_items