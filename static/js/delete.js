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
                // Delete buttons are now in the 3-dot menu
                // No need to add separate delete buttons
            }
        })
        .catch(err => console.error('Failed to check delete status:', err));
}

/**
 * Confirm deletion
 */
function confirmDelete(path, name, type) {
    const message = type === 'folder' 
        ? `Delete folder "${name}" and all its contents?\n\nThis action cannot be undone!`
        : `Delete file "${name}"?\n\nThis action cannot be undone!`;
    
    if (!confirm(message)) {
        return;
    }
    
    // If password required, prompt for it
    let password = null;
    if (deletePasswordRequired) {
        password = prompt('Enter delete password:');
        if (password === null) {
            return; // Cancelled
        }
    }
    
    deleteItem(path, password);
}

/**
 * Delete item via API
 */
async function deleteItem(path, password) {
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
            alert(result.message);
            location.reload();
        } else {
            alert('Delete failed: ' + result.message);
        }
    } catch (error) {
        alert('Delete error: ' + error.message);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initDelete);
