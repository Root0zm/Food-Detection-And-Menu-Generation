// Biến toàn cục để lưu link ảnh tạm
let currentImageUrl = "";

// 1. Hàm gửi ảnh lên Server để AI phân tích
async function analyzeFood() {
    const fileInput = document.getElementById('imageInput');
    const loadingDiv = document.getElementById('loading');
    const editorArea = document.getElementById('editorArea');
    
    // Validate input
    if (fileInput.files.length === 0) {
        alert("Vui lòng chọn ảnh trước!");
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    // UI: Bật loading, ẩn editor cũ
    loadingDiv.classList.remove('hidden');
    editorArea.classList.add('hidden');

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        
        // Tắt loading
        loadingDiv.classList.add('hidden');

        if (data.success) {
            currentImageUrl = data.image_url;

            // Đổ dữ liệu vào Form Editor (Cột Trái) để người dùng sửa
            document.getElementById('editImg').src = currentImageUrl;
            document.getElementById('editName').value = data.data.dish_name;
            document.getElementById('editPrice').value = data.data.price; 
            document.getElementById('editDesc').value = data.data.description;
            document.getElementById('editNutri').value = data.data.nutrition_summary;

            // Hiện Form Editor lên
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

// 2. Hàm chuyển món từ Editor sang Menu (Cột Phải)
function addToMenu() {
    // Lấy dữ liệu đã chỉnh sửa
    const name = document.getElementById('editName').value;
    const price = document.getElementById('editPrice').value;
    const desc = document.getElementById('editDesc').value;
    const nutri = document.getElementById('editNutri').value;
    const imgUrl = document.getElementById('editImg').src;

    if (!name) { alert("Tên món không được để trống!"); return; }

    // Xóa dòng "Chưa có món nào..." nếu đang có
    const menuContainer = document.getElementById('menuContainer');
    const emptyState = menuContainer.querySelector('.empty-state');
    if (emptyState) { emptyState.remove(); }

    // Tạo HTML cho hàng menu mới (Row Layout)
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

    // Chèn vào đầu danh sách
    menuContainer.insertAdjacentHTML('afterbegin', menuItemHTML);
    
    // (Tùy chọn) Reset form bên trái sau khi thêm xong
    // document.getElementById('editorArea').classList.add('hidden');
}

// 3. Hàm xóa món ăn
function removeMenuItem(button) {
    if (confirm("Bạn có chắc muốn xóa món này không?")) {
        // Tìm thẻ cha (menu-item-row) và xóa nó đi
        const itemRow = button.closest('.menu-item-row');
        itemRow.remove();

        // Nếu xóa hết thì hiện lại thông báo Empty
        const menuContainer = document.getElementById('menuContainer');
        if (menuContainer.children.length === 0) {
            menuContainer.innerHTML = '<div class="empty-state">Chưa có món nào trong menu. Hãy quét ảnh bên trái!</div>';
        }
    }
}