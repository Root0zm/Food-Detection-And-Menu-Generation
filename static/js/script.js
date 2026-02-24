let currentImageUrl = "";

async function analyzeFood() {
    const fileInput = document.getElementById('imageInput');
    const loadingDiv = document.getElementById('loading');
    const editorArea = document.getElementById('editorArea');

    if (fileInput.files.length === 0) {
        alert("Vui lòng chọn ảnh trước!");
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    loadingDiv.classList.remove('hidden');
    editorArea.classList.add('hidden');

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
            document.getElementById('editPrice').value = data.data.price;
            document.getElementById('editDesc').value = data.data.description;
            document.getElementById('editNutri').value = data.data.nutrition_summary;
            editorArea.classList.remove('hidden');
        } else {
            alert("Lỗi từ Server: " + data.message);
        }

    } catch (error) {
        console.error("Error:", error);
        loadingDiv.classList.add('hidden');
        alert("Không thể kết nối đến Server.");
    }
}