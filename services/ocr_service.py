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
        # Với bản mới, các tham số cấu hình thường được nhận tự động hoặc qua config file.
        # Ta khởi tạo đơn giản nhất để tránh lỗi tham số lạ.
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
            # --- 1. CHẠY OCR (Dùng .predict theo yêu cầu của thư viện) ---
            # KHÔNG truyền cls=True vào đây nữa
            results = self.ocr.predict(img_path)
            
            raw_texts = []
            
            # --- 2. XỬ LÝ KẾT QUẢ (Structure mới) ---
            # Kết quả trả về là một list các object, mỗi object chứa thông tin nhận diện
            for res in results:
                # Kiểm tra xem object có thuộc tính 'rec_texts' không (đây là đặc trưng bản mới)
                if hasattr(res, 'rec_texts'):
                    if res.rec_texts:
                        for text in res.rec_texts:
                            if text:
                                raw_texts.append(str(text))
                                
                # Dự phòng: Nếu nó trả về Dictionary (một số version khác)
                elif isinstance(res, dict) and 'rec_texts' in res:
                    raw_texts.extend(res['rec_texts'])

            # --- 3. BỘ LỌC RÁC (Giữ nguyên logic cũ) ---
            clean_texts = []
            for text in raw_texts:
                text = text.strip()
                if not text: continue
                
                if text.lower() in ['k', 'đ', 'd', '$', 'vnd', 'xu']:
                    clean_texts.append(text)
                    continue

                # Lọc rác: Bỏ qua chuỗi ngắn (trừ số) & ký tự lạ
                if len(text) < 2 and not re.search(r'\d', text):
                    continue
                if not re.search(r'[a-zA-Z0-9àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', text):
                    continue

                clean_texts.append(text)

            return clean_texts

        except Exception as e:
            print(f"❌ Lỗi OCR Service: {e}")
            # In chi tiết lỗi để debug nếu cần
            import traceback
            traceback.print_exc()
            return []

 #--- TEST CODE ---

#if __name__ == "__main__":
 #   service = OCRService()
  #  test_path = r"static/debug/bunbohue.png" 
  #  print(f"🔍 Đang đọc: {test_path}")
  #  texts = service.extract_text(test_path)
  #  
  #  print("-" * 30)
  #  print(f"✅ KẾT QUẢ ({len(texts)} dòng):")
  #  for t in texts:
  #      print(f"  - {t}") ##
