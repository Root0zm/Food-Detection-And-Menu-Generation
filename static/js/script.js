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

function addToMenu() {
    const name = document.getElementById('editName').value;
    const price = document.getElementById('editPrice').value;
    const desc = document.getElementById('editDesc').value;
    const nutri = document.getElementById('editNutri').value;
    const imgUrl = document.getElementById('editImg').src;

    if (!name) { alert("Tên món không được để trống!"); return; }

    const menuContainer = document.getElementById('menuContainer');
    const emptyState = menuContainer.querySelector('.empty-state');
    if (emptyState) { emptyState.remove(); }

    const menuItemHTML = `
        <div class="menu-item-row">
            <img src="${imgUrl}" class="menu-item-img" alt="${name}">
            
            <div class="menu-item-content">
                <div class="row-header">
                    <span class="dish-name">${name}</span>
                    <span class="dish-price">${price}</span>
                </div>
                
                <div class="row-desc">
                    <span class="label">Mô tả:</span>
                    ${desc}
                </div>

                <div class="row-nutri">
                    <span class="label">Dinh dưỡng:</span>
                    ${nutri}
                </div>
            </div>

            <button class="btn-delete" onclick="removeMenuItem(this)" title="Xóa món này">✕</button>
        </div>
    `;
    menuContainer.insertAdjacentHTML('afterbegin', menuItemHTML);
    
}

function removeMenuItem(button) {
    if (confirm("Bạn có chắc muốn xóa món này không?")) {
        const itemRow = button.closest('.menu-item-row');
        itemRow.remove();
        const menuContainer = document.getElementById('menuContainer');
        if (menuContainer.children.length === 0) {
            menuContainer.innerHTML = '<div class="empty-state">Chưa có món nào trong menu. Hãy quét ảnh bên trái!</div>';
        }
    }
}