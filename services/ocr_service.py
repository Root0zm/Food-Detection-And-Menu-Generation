import os
import sys

# Khống chế OpenMP và MKL threads để tránh deadlock khi chạy PaddleOCR trong Flask thread
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

# Disable oneDNN/MKLDNN to prevent CPU inference hangs in PaddlePaddle 3.x
os.environ["FLAGS_use_onednn"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "0"

import site
import re

# Windows DLL loading resolution for NVIDIA CUDA libraries in virtual environment site-packages
if sys.platform == 'win32':
    try:
        print("🔍 [OCR Service] Resolving NVIDIA DLLs...")
        for sp in site.getsitepackages():
            nvidia_dir = os.path.join(sp, 'nvidia')
            if os.path.exists(nvidia_dir):
                for root, dirs, files in os.walk(nvidia_dir):
                    if root.endswith('bin'):
                        try:
                            print(f"   Adding DLL directory: {root}")
                            os.add_dll_directory(root)
                        except Exception as e:
                            print(f"   Error adding {root}: {e}")
    except Exception as e:
        print(f"❌ Error in DLL resolution code: {e}")

from paddleocr import PaddleOCR
from typing import List
import logging

# Tắt log rác
logging.getLogger("ppocr").setLevel(logging.ERROR)
logging.getLogger("paddle").setLevel(logging.ERROR)

class OCRService:
    def __init__(self):
        """Khởi tạo PaddleOCR cho phiên bản Pipeline mới với hỗ trợ GPU tự động."""
        import paddle
        use_gpu = paddle.is_compiled_with_cuda()
        print(f"Khởi tạo PaddleOCR - GPU: {use_gpu}")
        self.ocr = PaddleOCR(
            lang='vi', 
            use_textline_orientation=False, 
            use_doc_orientation_classify=False,
            use_doc_unwarping=False
        )

    def extract_text(self, img_path: str) -> List[str]:
        """
        Trích xuất văn bản từ ảnh và lọc rác.
        Tự động thu nhỏ ảnh (max_dim = 720) để tăng tốc độ xử lý CPU lên gấp nhiều lần và giảm tải RAM.
        """
        if not os.path.exists(img_path):
            print(f"Không tìm thấy file ảnh: {img_path}")
            return []

        try:
            import cv2
            img = cv2.imread(img_path)
            if img is None:
                print(f" Không đọc được file ảnh bằng OpenCV: {img_path}")
                return []
                
            h, w = img.shape[:2]
            max_dim = 720
            scale = 1.0
            ocr_input_path = img_path
            temp_path = None
            
            if max(h, w) > max_dim:
                scale = max_dim / float(max(h, w))
                new_w = int(w * scale)
                new_h = int(h * scale)
                resized_img = cv2.resize(img, (new_w, new_h))
                
                # Tạo ảnh tạm để đưa vào OCR
                temp_filename = f"temp_ocr_scale_{os.path.basename(img_path)}"
                temp_path = os.path.join(os.path.dirname(img_path), temp_filename)
                cv2.imwrite(temp_path, resized_img)
                ocr_input_path = temp_path
                
            # Use predict method which works with PaddleX 3.0+ OCR pipeline
            results = self.ocr.predict(ocr_input_path)
            
            # Dọn dẹp ảnh tạm ngay lập tức
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            
            extracted_items = []
            
            for res in results:
                # The result is a dict-like OCRResult object containing 'rec_texts' and 'dt_polys'
                if isinstance(res, dict) and 'rec_texts' in res and 'dt_polys' in res:
                    texts = res['rec_texts']
                    polys = res['dt_polys']
                    
                    for text, poly in zip(texts, polys):
                        text = text.strip()
                        if not text: continue
                        
                        # Convert numpy array to list
                        poly_list = poly.tolist() if hasattr(poly, 'tolist') else poly
                        
                        # Quy đổi ngược tọa độ về kích thước ảnh gốc
                        if scale != 1.0:
                            box = [[pt[0] / scale, pt[1] / scale] for pt in poly_list]
                        else:
                            box = poly_list
                        
                        # Apply the same filtering rules as before
                        if text.lower() in ['k', 'đ', 'd', '$', 'vnd', 'xu']:
                            extracted_items.append({'text': text, 'box': box})
                            continue

                        if len(text) < 2 and not re.search(r'\d', text):
                            continue
                        if not re.search(r'[a-zA-Z0-9àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', text):
                            continue

                        extracted_items.append({'text': text, 'box': box})

            return extracted_items

        except Exception as e:
            print(f" Lỗi OCR Service: {e}")
            import traceback
            traceback.print_exc()
            return []

 #--- TEST CODE ---

#if __name__ == "__main__":
 #   service = OCRService()
  #  test_path = r"static/debug/bunbohue.png" 
  #  print(f" Đang đọc: {test_path}")
  #  texts = service.extract_text(test_path)
  #  
  #  print("-" * 30)
  #  print(f" KẾT QUẢ ({len(texts)} dòng):")
  #  for t in texts:
  #      print(f"  - {t}") ##
