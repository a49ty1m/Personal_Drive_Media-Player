/**
 * menu.js - 3-dot menu and file preview functionality
 */

/**
 * Click on file name to preview/play
 */
function clickFile(fileId) {
    const fileItem = document.getElementById(fileId);
    const path = fileItem.dataset.path;
    const extension = fileItem.dataset.extension;
    const isVideo = fileItem.dataset.isVideo === 'True';
    const url = fileItem.dataset.url;
    
    if (isVideo) {
        // Play video in player
        window.location.href = url;
    } else {
        // Preview other file types
        previewFile(path, extension);
    }
}

/**
 * Toggle dropdown menu
 */
function toggleMenu(event, fileId) {
    event.stopPropagation();
    const menuId = 'menu-' + fileId;
    const menu = document.getElementById(menuId);
    
    // Close all other menus
    document.querySelectorAll('.dropdown-menu').forEach(m => {
        if (m.id !== menuId) {
            m.classList.remove('show');
        }
    });
    
    // Toggle current menu
    menu.classList.toggle('show');
}

/**
 * Close menu
 */
function closeMenu() {
    document.querySelectorAll('.dropdown-menu').forEach(menu => {
        menu.classList.remove('show');
    });
}

/**
 * Close menu when clicking outside
 */
document.addEventListener('click', function(event) {
    if (!event.target.closest('.menu-dots')) {
        closeMenu();
    }
});

/**
 * Open file (for videos)
 */
function openFile(url) {
    closeMenu();
    window.location.href = url;
}

/**
 * Open folder
 */
function openFolder(url) {
    closeMenu();
    window.location.href = url;
}

/**
 * Download file
 */
function downloadFile(path, filename) {
    closeMenu();
    const downloadUrl = '/download/' + encodeURIComponent(path) + '?download=true';
    
    // Create temporary link and trigger download
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

/**
 * Preview file based on type
 */
function previewFile(path, extension) {
    closeMenu();
    const ext = extension.toLowerCase();
    
    // Check if it's a previewable type
    const imageTypes = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.ico'];
    const textTypes = ['.txt', '.md', '.json', '.xml', '.csv', '.log', '.py', '.js', '.html', '.css', '.yml', '.yaml', '.sh', '.conf', '.ini', '.cfg'];
    const pdfTypes = ['.pdf'];
    const audioTypes = ['.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac'];
    
    if (imageTypes.includes(ext)) {
        previewImage(path);
    } else if (textTypes.includes(ext)) {
        previewText(path);
    } else if (pdfTypes.includes(ext)) {
        // Try to preview PDF, with fallback
        previewPDFWithFallback(path);
    } else if (audioTypes.includes(ext)) {
        previewAudio(path);
    } else {
        // Not previewable, show message and download
        showPreviewNotAvailable(path, ext);
    }
}

/**
 * Show "preview not available" message with download option
 */
function showPreviewNotAvailable(path, extension) {
    const filename = path.split('/').pop();
    currentPreviewPath = path;
    currentPreviewFilename = filename;
    
    const modal = createPreviewModal(filename);
    
    modal.querySelector('.preview-content').innerHTML = `
        <div style="text-align: center; padding: 60px 20px;">
            <div style="font-size: 64px; margin-bottom: 20px;">📎</div>
            <h3 style="color: #e0e0e0; margin-bottom: 10px;">Preview not available</h3>
            <p style="color: #888; margin-bottom: 30px;">
                ${extension.toUpperCase()} files cannot be previewed in the browser.
            </p>
            <button class="btn-primary" onclick="downloadCurrentPreview(); closePreviewModal();">
                ⬇️ Download File
            </button>
        </div>
    `;
    
    document.body.appendChild(modal);
    modal.classList.add('show');
}

/**
 * Preview PDF with fallback
 */
function previewPDFWithFallback(path) {
    const filename = path.split('/').pop();
    currentPreviewPath = path;
    currentPreviewFilename = filename;
    
    const modal = createPreviewModal(filename, false); // No custom zoom controls needed
    const downloadUrl = '/download/' + encodeURIComponent(path);
    
    // Try to embed PDF - browser has built-in zoom
    modal.querySelector('.preview-content').innerHTML = `
        <iframe id="pdf-viewer" src="${downloadUrl}#view=FitH" title="${escapeHtml(filename)}" onload="handlePDFLoad(this)" onerror="handlePDFError()"></iframe>
        <div id="pdf-fallback" style="display: none; text-align: center; padding: 60px 20px;">
            <div style="font-size: 64px; margin-bottom: 20px;">📄</div>
            <h3 style="color: #e0e0e0; margin-bottom: 10px;">PDF Preview Unavailable</h3>
            <p style="color: #888; margin-bottom: 30px;">
                Your browser cannot display this PDF inline.<br>
                Please download it to view.
            </p>
            <button class="btn-primary" onclick="downloadCurrentPreview(); closePreviewModal();">
                ⬇️ Download PDF
            </button>
        </div>
    `;
    
    document.body.appendChild(modal);
    modal.classList.add('show');
}

/**
 * Handle PDF load success
 */
function handlePDFLoad(iframe) {
    // PDF loaded successfully
    console.log('PDF preview loaded');
}

/**
 * Handle PDF load error
 */
function handlePDFError() {
    // Show fallback message
    const iframe = document.querySelector('.preview-content iframe');
    const fallback = document.getElementById('pdf-fallback');
    if (iframe && fallback) {
        iframe.style.display = 'none';
        fallback.style.display = 'block';
    }
}

/**
 * Preview image
 */
function previewImage(path) {
    const filename = path.split('/').pop();
    currentPreviewPath = path;
    currentPreviewFilename = filename;
    
    const modal = createPreviewModal(filename, false); // false = no zoom controls for images
    const downloadUrl = '/download/' + encodeURIComponent(path);
    
    modal.querySelector('.preview-content').innerHTML = `
        <img src="${downloadUrl}" alt="${escapeHtml(filename)}">
    `;
    
    document.body.appendChild(modal);
    modal.classList.add('show');
}

/**
 * Preview text file
 */
async function previewText(path) {
    const filename = path.split('/').pop();
    currentPreviewPath = path;
    currentPreviewFilename = filename;
    
    const modal = createPreviewModal(filename, false); // false = no zoom controls
    const downloadUrl = '/download/' + encodeURIComponent(path);
    
    try {
        const response = await fetch(downloadUrl);
        const text = await response.text();
        
        // Limit preview to first 50KB for performance
        const previewText = text.length > 50000 
            ? text.substring(0, 50000) + '\n\n... (file truncated for preview, download to view full content)'
            : text;
        
        modal.querySelector('.preview-content').innerHTML = `
            <pre>${escapeHtml(previewText)}</pre>
        `;
        
        document.body.appendChild(modal);
        modal.classList.add('show');
    } catch (error) {
        alert('Failed to load file preview: ' + error.message);
    }
}

/**
 * Preview PDF (legacy - use previewPDFWithFallback instead)
 */
function previewPDF(path) {
    previewPDFWithFallback(path);
}

/**
 * Preview audio
 */
function previewAudio(path) {
    const filename = path.split('/').pop();
    currentPreviewPath = path;
    currentPreviewFilename = filename;
    
    const modal = createPreviewModal(filename, false); // false = no zoom controls
    const downloadUrl = '/download/' + encodeURIComponent(path);
    
    modal.querySelector('.preview-content').innerHTML = `
        <div style="padding: 40px; text-align: center;">
            <h3 style="margin-bottom: 20px; color: #e0e0e0;">🎵 ${escapeHtml(filename)}</h3>
            <audio controls style="width: 100%; max-width: 600px;">
                <source src="${downloadUrl}">
                Your browser does not support the audio element.
            </audio>
        </div>
    `;
    
    document.body.appendChild(modal);
    modal.classList.add('show');
}

/**
 * Create preview modal
 */
function createPreviewModal(filename, isPDF = false) {
    const modal = document.createElement('div');
    modal.className = 'modal preview-modal';
    
    // Add zoom controls for PDF
    const zoomControls = isPDF ? `
        <div class="pdf-zoom-controls">
            <button class="zoom-btn" onclick="zoomOutPDF()" title="Zoom Out">🔍−</button>
            <span id="pdf-zoom-level" class="zoom-level">100%</span>
            <button class="zoom-btn" onclick="zoomInPDF()" title="Zoom In">🔍+</button>
            <button class="zoom-btn" onclick="resetPDFZoom()" title="Reset Zoom">⟲</button>
        </div>
    ` : '';
    
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>📄 ${escapeHtml(filename)}</h2>
                <div class="modal-header-actions">
                    ${zoomControls}
                    <button class="preview-download-btn" onclick="downloadCurrentPreview()">⬇️ Download</button>
                    <button class="modal-close" onclick="closePreviewModal()">&times;</button>
                </div>
            </div>
            <div class="modal-body">
                <div class="preview-content">
                    <div class="loading">⏳ Loading preview...</div>
                </div>
            </div>
        </div>
    `;
    
    return modal;
}

// Store current preview path for download
let currentPreviewPath = null;
let currentPreviewFilename = null;

/**
 * Download current preview file
 */
function downloadCurrentPreview() {
    if (currentPreviewPath && currentPreviewFilename) {
        downloadFile(currentPreviewPath, currentPreviewFilename);
    }
}

/**
 * Close preview modal
 */
function closePreviewModal() {
    const modal = document.querySelector('.preview-modal');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => modal.remove(), 300);
    }
    // Reset PDF zoom level
    pdfZoomLevel = 100;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Close preview modal when clicking outside
document.addEventListener('click', function(event) {
    const modal = document.querySelector('.preview-modal');
    if (modal && event.target === modal) {
        closePreviewModal();
    }
});

// Close preview modal on escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closePreviewModal();
    }
});
