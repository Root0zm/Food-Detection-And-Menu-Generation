let currentImageUrl = "";

let stream = null;
let capturedFile = null; 

document.getElementById('imageInput').addEventListener('change', function() {
    capturedFile = null; 
    if (this.files.length > 0) {
        analyzeFood(); 
    }
});

async function startCamera() {
    const cameraContainer = document.getElementById('cameraContainer');
    const video = document.getElementById('videoElement');
    
    try {
        stream = await navigator.mediaDevices.getUserMedia({ 
            video: { facingMode: 'environment' } 
        });
        video.srcObject = stream;
        cameraContainer.classList.remove('hidden'); 
    } catch (err) {
        console.error("Lỗi xin quyền camera:", err);
        alert("Không thể mở Camera! Hãy đảm bảo bạn đã cấp quyền trong trình duyệt.");
    }
}

function stopCamera() {
    const cameraContainer = document.getElementById('cameraContainer');
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
    cameraContainer.classList.add('hidden'); 
}

function capturePhoto() {
    const video = document.getElementById('videoElement');
    const canvas = document.getElementById('canvasElement');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);  

    canvas.toBlob(function(blob) {
        capturedFile = new File([blob], "camera_capture.jpg", { type: "image/jpeg" });
        
        // Thông báo và dọn dẹp
        alert("📸 Đã chụp ảnh thành công! Hãy bấm 'Quét ảnh' để AI phân tích.");
        document.getElementById('imageInput').value = ""; 
        stopCamera(); 
        analyzeFood();
        
    }, 'image/jpeg', 0.9); 
}

async function analyzeFood() {
    const fileInput = document.getElementById('imageInput');
    const loadingDiv = document.getElementById('loading');
    const editorArea = document.getElementById('editorArea');


    let fileToUpload = null;
    if (capturedFile) {
        fileToUpload = capturedFile;
    } else if (fileInput.files.length > 0) {
        fileToUpload = fileInput.files[0];
    }

    if (!fileToUpload) {
        alert("Vui lòng chọn ảnh hoặc chụp ảnh trước!");
        return;
    }

    const formData = new FormData();
    formData.append('file', fileToUpload);
    loadingDiv.classList.remove('hidden');
    editorArea.classList.add('hidden');
    loadingDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        loadingDiv.classList.add('hidden');

        if (data.success) {
            currentImageUrl = data.image_url;
            document.getElementById('editImg').src = currentImageUrl;
            document.getElementById('editName').value = data.data.dish_name;
            let rawPrice = String(data.data.price);
            let numericPrice = parseInt(rawPrice.replace(/\D/g, ''), 10);
            if (!isNaN(numericPrice)) {
            document.getElementById('editPrice').value = numericPrice.toLocaleString('en-US') + " VND";
            } 
            else {
            document.getElementById('editPrice').value = rawPrice;
            }
            document.getElementById('editDesc').value = data.data.description;
            document.getElementById('editNutri').value = data.data.nutrition_summary;      
            editorArea.classList.remove('hidden');
            editorArea.scrollIntoView({ behavior: 'smooth', block: 'start' });
            
            capturedFile = null; 
            fileInput.value = ""; 
        } else {
            alert("Lỗi từ Server: " + data.message);
        }

    } catch (error) {
        console.error("Error:", error);
        loadingDiv.classList.add('hidden');
        alert("Không thể kết nối đến Server.");
    }
}


