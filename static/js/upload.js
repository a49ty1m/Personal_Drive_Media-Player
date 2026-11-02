/**
 * upload.js - File upload functionality
 */

// Upload modal state
let uploadModal = null;
let currentPath = "";

/**
 * Initialize upload functionality
 */
function initUpload() {
    currentPath = document.body.dataset.currentPath || "";
    
    // Check if upload is enabled
    fetch('/api/upload/check')
        .then(res => res.json())
        .then(data => {
            if (data.enabled) {
                // Just create modal, button already exists in HTML
                createUploadModal(data.password_required, data.max_size_mb);
            }
        })
        .catch(err => console.error('Failed to check upload status:', err));
}

/**
 * Show upload modal (called from HTML button)
 */
function showUploadModal() {
    openUploadModal();
}

/**
 * Create upload modal
 */
function createUploadModal(passwordRequired, maxSizeMB) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.id = 'uploadModal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>Upload Files</h2>
                <button class="modal-close" onclick="closeUploadModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="upload-zone" id="uploadZone">
                    <div class="upload-icon">📁</div>
                    <p>Drag & drop files here or click to browse</p>
                    <p class="upload-limit">Max size: ${maxSizeMB} MB per file</p>
                    <input type="file" id="fileInput" multiple hidden>
                </div>
                ${passwordRequired ? `
                <div class="form-group">
                    <label for="uploadPassword">Password:</label>
                    <input type="password" id="uploadPassword" placeholder="Enter upload password">
                </div>
                ` : ''}
                <div id="fileList" class="file-list-upload"></div>
                <div id="uploadProgress" class="upload-progress hidden">
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressFill"></div>
                    </div>
                    <p id="progressText">Uploading...</p>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn-cancel" onclick="closeUploadModal()">Cancel</button>
                <button class="btn-primary" id="uploadButton" onclick="startUpload()" disabled>Upload</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    uploadModal = modal;
    
    // Setup drag & drop
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');
    
    uploadZone.onclick = () => fileInput.click();
    
    uploadZone.ondragover = (e) => {
        e.preventDefault();
        uploadZone.classList.add('drag-over');
    };
    
    uploadZone.ondragleave = () => {
        uploadZone.classList.remove('drag-over');
    };
    
    uploadZone.ondrop = (e) => {
        e.preventDefault();
        uploadZone.classList.remove('drag-over');
        handleFiles(e.dataTransfer.files);
    };
    
    fileInput.onchange = (e) => {
        handleFiles(e.target.files);
    };
}

/**
 * Handle selected files
 */
function handleFiles(files) {
    const fileList = document.getElementById('fileList');
    const uploadButton = document.getElementById('uploadButton');
    
    if (files.length === 0) return;
    
    fileList.innerHTML = '<h3>Selected Files:</h3>';
    
    Array.from(files).forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item-upload';
        fileItem.innerHTML = `
            <span class="file-icon">📎</span>
            <span class="file-name">${file.name}</span>
            <span class="file-size">${formatFileSize(file.size)}</span>
        `;
        fileList.appendChild(fileItem);
    });
    
    uploadButton.disabled = false;
    uploadButton.dataset.files = JSON.stringify(Array.from(files).map(f => f.name));
}

/**
 * Start upload
 */
async function startUpload() {
    const fileInput = document.getElementById('fileInput');
    const passwordInput = document.getElementById('uploadPassword');
    const uploadButton = document.getElementById('uploadButton');
    const uploadProgress = document.getElementById('uploadProgress');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    
    if (fileInput.files.length === 0) return;
    
    const formData = new FormData();
    
    Array.from(fileInput.files).forEach(file => {
        formData.append('files[]', file);
    });
    
    formData.append('path', currentPath);
    
    if (passwordInput) {
        formData.append('password', passwordInput.value);
    }
    
    uploadButton.disabled = true;
    uploadProgress.classList.remove('hidden');
    
    try {
        const xhr = new XMLHttpRequest();
        
        xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) {
                const percent = (e.loaded / e.total) * 100;
                progressFill.style.width = percent + '%';
                progressText.textContent = `Uploading... ${Math.round(percent)}%`;
            }
        };
        
        xhr.onload = () => {
            if (xhr.status === 200) {
                const result = JSON.parse(xhr.responseText);
                alert(result.message);
                if (result.success) {
                    location.reload();
                }
            } else {
                const error = JSON.parse(xhr.responseText);
                alert('Upload failed: ' + error.message);
            }
            uploadButton.disabled = false;
            uploadProgress.classList.add('hidden');
        };
        
        xhr.onerror = () => {
            alert('Upload failed. Please try again.');
            uploadButton.disabled = false;
            uploadProgress.classList.add('hidden');
        };
        
        xhr.open('POST', '/api/upload');
        xhr.send(formData);
        
    } catch (error) {
        alert('Upload error: ' + error.message);
        uploadButton.disabled = false;
        uploadProgress.classList.add('hidden');
    }
}

/**
 * Open upload modal
 */
function openUploadModal() {
    if (uploadModal) {
        uploadModal.classList.add('show');
    }
}

/**
 * Close upload modal
 */
function closeUploadModal() {
    if (uploadModal) {
        uploadModal.classList.remove('show');
        // Reset
        document.getElementById('fileInput').value = '';
        document.getElementById('fileList').innerHTML = '';
        document.getElementById('uploadButton').disabled = true;
        document.getElementById('uploadProgress').classList.add('hidden');
    }
}

/**
 * Format file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initUpload);
