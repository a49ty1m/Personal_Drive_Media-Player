/**
 * delete.js - File and folder deletion functionality
 */

console.log('✓ delete.js loaded successfully');

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
    console.log('deleteFile called:', { path, name });
    performDeletion(path, name, 'file');
}

/**
 * Delete folder (called from browse.html after confirmation)
 */
function deleteFolder(path, name) {
    console.log('deleteFolder called:', { path, name });
    performDeletion(path, name, 'folder');
}

// Make functions globally accessible
window.deleteFile = deleteFile;
window.deleteFolder = deleteFolder;

/**
 * Perform the actual deletion
 */
async function performDeletion(path, name, type) {
    console.log('performDeletion called:', { path, name, type });
    
    // If password required, prompt for it
    let password = null;
    if (deletePasswordRequired) {
        password = prompt('Enter delete password:');
        if (password === null) {
            console.log('Delete cancelled by user');
            return; // Cancelled
        }
    }
    
    try {
        console.log('Sending delete request...');
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
        
        console.log('Response status:', response.status);
        const result = await response.json();
        console.log('Response data:', result);
        
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

/**
 * Show notification (reuse ZIP notification element)
 */
function showNotification(message, type) {
    const notification = document.getElementById('zipNotification');
    if (!notification) {
        console.error('Notification element not found');
        alert(message); // Fallback
        return;
    }
    
    const titleEl = notification.querySelector('.zip-notification-title');
    const subtitleEl = notification.querySelector('.zip-notification-subtitle');
    const spinner = notification.querySelector('.zip-spinner');
    
    if (!titleEl || !subtitleEl || !spinner) {
        console.error('Notification elements not found');
        alert(message); // Fallback
        return;
    }
    
    // Hide spinner for success/error
    spinner.style.display = 'none';
    
    titleEl.textContent = message;
    subtitleEl.textContent = '';
    
    if (type === 'success') {
        titleEl.style.color = '#10b981';
    } else if (type === 'error') {
        titleEl.style.color = '#ef4444';
    }
    
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
        // Reset styles
        setTimeout(() => {
            spinner.style.display = 'block';
            titleEl.style.color = '#e0e0e0';
        }, 300);
    }, 2000);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initDelete);
