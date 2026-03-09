
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
    const selectedLang = document.getElementById('outputLanguage').value;

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
    formData.append('language', selectedLang);
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
            
            // Hiển thị tags WIP 
            const tagsDiv = document.getElementById('editTags');
            tagsDiv.innerHTML = ''; 
            if (data.data.tags && data.data.tags.length > 0) {
                data.data.tags.forEach(tag => {
                    const span = document.createElement('span');
                    span.className = 'smart-tag';
                    span.innerText = tag;
                    tagsDiv.appendChild(span);
                });
            }




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


function switchTab(tabId) {
     document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.add('hidden');
    });
    
    
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
     document.getElementById(tabId).classList.remove('hidden');
    
     document.getElementById('btn-' + tabId).classList.add('active');
    
     window.scrollTo({ top: 0, behavior: 'smooth' });
}
 
 let menuItems = JSON.parse(localStorage.getItem('myRestaurantMenu')) || [];

 document.addEventListener('DOMContentLoaded', () => {
    renderMenu();
});

 async function analyzeForMenu(inputElement) {
    if (!inputElement.files || inputElement.files.length === 0) return;
    
    const file = inputElement.files[0];
    const loadingDiv = document.getElementById('menuLoading');
    const selectedLang = document.getElementById('outputLanguage').value;
    loadingDiv.classList.remove('hidden');
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('language', selectedLang);
    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        loadingDiv.classList.add('hidden');

        if (data.success) {
             let rawPrice = String(data.data.price);
            let numericPrice = parseInt(rawPrice.replace(/\D/g, ''), 10);
            let formattedPrice = !isNaN(numericPrice) ? numericPrice.toLocaleString('en-US') + " VND" : rawPrice;

             const newItem = {
                id: Date.now(),  
                imageUrl: data.image_url,
                name: data.data.dish_name,
                price: formattedPrice,
                description: data.data.description,
                nutrition: data.data.nutrition_summary,

                tags: data.data.tags || []
            };

             menuItems.push(newItem);
            localStorage.setItem('myRestaurantMenu', JSON.stringify(menuItems));
            
             renderMenu();
            
             inputElement.value = "";
        } else {
            alert("Server Error: " + data.message);
        }

    } catch (error) {
        console.error("Error:", error);
        loadingDiv.classList.add('hidden');
        alert("Cannot connect to the server. Please try again later.");
    }
}

 function removeFromMenu(id) {
    menuItems = menuItems.filter(item => item.id !== id);
    localStorage.setItem('myRestaurantMenu', JSON.stringify(menuItems));
    renderMenu();
}

 function renderMenu() {
    const listContainer = document.getElementById('menuList');
    listContainer.innerHTML = ''; 

    if (menuItems.length === 0) {
        listContainer.innerHTML = '<p class="empty-menu-msg">Your menu is empty. Add some dishes!</p>';
        return;
    }

    menuItems.forEach(item => {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'menu-item';

        // Delete if needed
        let tagsHtml = '';
        if (item.tags && item.tags.length > 0) {
            tagsHtml = '<div class="tags-container" style="margin-bottom: 10px;">' + 
                       item.tags.map(t => `<span class="smart-tag">${t}</span>`).join('') + 
                       '</div>';
        }



        // remove tagsHTML if you want to hide tags in menu list
        itemDiv.innerHTML = `
            <img src="${item.imageUrl}" alt="${item.name}" class="menu-item-img">
            <div class="menu-item-info">
                <div class="menu-item-header">
                    <h4 class="menu-item-name" contenteditable="true" onblur="updateMenuItem(${item.id}, 'name', this.innerText)" title="Click to edit">${item.name}</h4>
                    <span class="menu-item-price" contenteditable="true" onblur="updateMenuItem(${item.id}, 'price', this.innerText)" title="Click to edit">${item.price}</span>
                </div>
                ${tagsHtml}
                <p class="menu-item-desc" contenteditable="true" onblur="updateMenuItem(${item.id}, 'description', this.innerText)" title="Click to edit">${item.description}</p>
                <p class="menu-item-nutri" contenteditable="true" onblur="updateMenuItem(${item.id}, 'nutrition', this.innerText.replace('Nutrition: ', ''))" title="Click to edit">Nutrition: ${item.nutrition}</p>
            </div>
            <button onclick="removeFromMenu(${item.id})" class="remove-btn">✖ Remove</button>
        `;
        listContainer.appendChild(itemDiv);
    });
}

 function exportToPDF() {
    if (menuItems.length === 0) {
        alert("Cannot export an empty menu!");
        return;
    }
    
     window.print();
}

function updateMenuItem(id, field, newValue) {
    const itemIndex = menuItems.findIndex(item => item.id === id);
    if (itemIndex > -1) {
        menuItems[itemIndex][field] = newValue;
        localStorage.setItem('myRestaurantMenu', JSON.stringify(menuItems));
    }
}

function changeTheme() {
    const selectBox = document.getElementById('menuTheme');
    const bgImage = document.getElementById('printBgImage');
    const pdfArea = document.getElementById('pdfArea');
    const restaurantTitle = document.getElementById('restaurantName'); 
    const selectedUrl = selectBox.value;

    pdfArea.className = 'pdf-container'; 
    restaurantTitle.style.marginLeft = "0"; 
    restaurantTitle.style.borderBottom = "";

    restaurantTitle.style.marginLeft = "0";       
    restaurantTitle.style.marginRight = "0";     
    restaurantTitle.style.borderBottom = "";      
    pdfArea.classList.remove('theme-08');

    if (selectedUrl === "none") {
        bgImage.style.display = "none";
        bgImage.src = "";
        
   
        restaurantTitle.style.color = "#2c3e50"; 
        restaurantTitle.style.borderBottomColor = "#2c3e50";
    } else {
        bgImage.src = selectedUrl;
        bgImage.style.display = "block";
        
   
        if (selectedUrl.includes("06")) { 
         
            restaurantTitle.style.color = "#6d301f"; 
            
            restaurantTitle.style.borderBottomColor = "#6d301f";
           
        } 
        else if (selectedUrl.includes("08")) { 
         
            restaurantTitle.style.color = "#ffffff"; 
            restaurantTitle.style.marginLeft = "150px";
            restaurantTitle.style.borderBottom = "none";
            pdfArea.classList.add('theme-08');
            
        } 
        else if (selectedUrl.includes("07")) { 
         
            restaurantTitle.style.color = "#4673e5"; 
            restaurantTitle.style.marginRight = "180px";
            restaurantTitle.style.borderBottom = "none";
            restaurantTitle.style.fontFamily = "'Montserrat', serif";
            pdfArea.classList.add('theme-08');
        }
        else if (selectedUrl.includes("05")) { 
         
            restaurantTitle.style.color = "#dfebb1"; 
            restaurantTitle.style.borderBottom = "none";
            pdfArea.classList.add('theme-08');  
        }
    }
}


function limitTitleLength(event) {
    const title = event.target;
    if (event.key === 'Enter') {
        event.preventDefault();
        return;
    }
    const allowedKeys = ['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'];
    if (title.innerText.length >= 32 && !allowedKeys.includes(event.key)) {
        event.preventDefault();
    }
}

document.addEventListener('DOMContentLoaded', function() { 
    changeTheme();
});

function updateUILanguage() {
    const selectedLang = document.getElementById('outputLanguage').value;
    localStorage.setItem('app_lang', selectedLang);

    const elements = document.querySelectorAll('[data-i18n]');

    if (uiTranslations[selectedLang]) {
        elements.forEach(el => {
            const key = el.getAttribute('data-i18n');
            
            if (uiTranslations[selectedLang][key]) {
                if (el.tagName === 'TITLE') {
                    document.title = uiTranslations[selectedLang][key];
                } else {
                    el.innerHTML = uiTranslations[selectedLang][key];
                }
            }
        });
    }
}

document.getElementById('outputLanguage').addEventListener('change', updateUILanguage);
document.addEventListener('DOMContentLoaded', function() {
    const savedLang = localStorage.getItem('app_lang');
    if (savedLang) {
        document.getElementById('outputLanguage').value = savedLang; 
    }

    updateUILanguage();
    if (typeof changeTheme === "function") {
        changeTheme();
    }
});