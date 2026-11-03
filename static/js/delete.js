/**
 * delete.js - File and folder deletion functionality
 */

let deletePasswordRequired = false;

/**
 * Initialize delete functionality
 */
function initDelete() {
    // Check if delete is enabled
    fetch('/api/delete/check')
        .then(res => res.json())
        .then(data => {
            if (data.enabled) {
                deletePasswordRequired = data.password_required;
            }
        })
        .catch(err => console.error('Failed to check delete status:', err));
}

/**
 * Delete file (called from browse.html after confirmation)
 */
function deleteFile(path, name) {
    performDeletion(path, name, 'file');
}

/**
 * Delete folder (called from browse.html after confirmation)
 */
function deleteFolder(path, name) {
    performDeletion(path, name, 'folder');
}

// Make functions globally accessible
window.deleteFile = deleteFile;
window.deleteFolder = deleteFolder;

/**
 * Perform the actual deletion
 */
async function performDeletion(path, name, type) {
    
    // If password required, prompt for it
    let password = null;
    if (deletePasswordRequired) {
        password = prompt('Enter delete password:');
        if (password === null) {
            return; // Cancelled
        }
    }
    
    try {
        const response = await fetch('/api/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                path: path,
                password: password
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Show success notification briefly
            showNotification('✓ ' + result.message, 'success');
            // Reload after a short delay
            setTimeout(() => location.reload(), 500);
        } else {
            showNotification('✗ Delete failed: ' + result.message, 'error');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showNotification('✗ Delete error: ' + error.message, 'error');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initDelete);
