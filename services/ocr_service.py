import os
import re
from paddleocr import PaddleOCR
from typing import List
import logging

# Tắt log rác
logging.getLogger("ppocr").setLevel(logging.ERROR)
logging.getLogger("paddle").setLevel(logging.ERROR)

class OCRService:
    def __init__(self):
        """Khởi tạo PaddleOCR cho phiên bản Pipeline mới."""
        self.ocr = PaddleOCR(lang='vi', use_textline_orientation=False, use_doc_orientation_classify=False,
    use_doc_unwarping=False)

    def extract_text(self, img_path: str) -> List[str]:
        """
        Trích xuất văn bản từ ảnh và lọc rác.
        """
        if not os.path.exists(img_path):
            print(f"❌ Không tìm thấy file ảnh: {img_path}")
            return []

        try:

            # Use predict method which works with PaddleX 3.0+ OCR pipeline
            results = self.ocr.predict(img_path)
            
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
                        box = poly.tolist() if hasattr(poly, 'tolist') else poly
                        
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
            print(f"❌ Lỗi OCR Service: {e}")
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
