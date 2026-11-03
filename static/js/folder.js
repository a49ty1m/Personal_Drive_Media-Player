/**
 * folder.js - Folder creation functionality
 */

// Show create folder modal
function showCreateFolderModal() {
    const modal = document.getElementById('folderModal');
    const input = document.getElementById('folderNameInput');
    
    if (modal && input) {
        input.value = '';
        modal.style.display = 'flex';
        input.focus();
    }
}

// Close create folder modal
function closeFolderModal() {
    const modal = document.getElementById('folderModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Create folder
async function createFolder() {
    const input = document.getElementById('folderNameInput');
    const folderName = input.value.trim();
    
    if (!folderName) {
        showNotification('⚠ Please enter a folder name', 'warning');
        return;
    }
    
    // Validate folder name (no special characters that could cause issues)
    if (!/^[a-zA-Z0-9_\-\.\s]+$/.test(folderName)) {
        showNotification('⚠ Folder name contains invalid characters', 'warning');
        return;
    }
    
    const currentPath = document.body.dataset.currentPath || '/';
    
    try {
        const response = await fetch('/api/folder/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                path: currentPath,
                name: folderName
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('✓ ' + (data.message || 'Folder created successfully'), 'success');
            closeFolderModal();
            
            // Reload page to show new folder
            setTimeout(() => {
                window.location.reload();
            }, 800);
        } else {
            showNotification('✗ ' + (data.message || 'Failed to create folder'), 'error');
        }
    } catch (error) {
        console.error('Error creating folder:', error);
        showNotification('✗ Network error while creating folder', 'error');
    }
}

// Handle Enter key in input field
document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('folderNameInput');
    if (input) {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                createFolder();
            }
        });
    }
    
    // Close modal when clicking outside
    const modal = document.getElementById('folderModal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeFolderModal();
            }
        });
    }
});

/**
 * Show notification (reuse ZIP notification element)
 */
function showNotification(message, type) {
    const notification = document.getElementById('zipNotification');
    if (!notification) {
        console.error('Notification element not found');
        return;
    }
    
    const titleEl = notification.querySelector('.zip-notification-title');
    const subtitleEl = notification.querySelector('.zip-notification-subtitle');
    const spinner = notification.querySelector('.zip-spinner');
    
    if (!titleEl || !subtitleEl || !spinner) {
        console.error('Notification elements not found');
        return;
    }
    
    // Hide spinner for success/error/warning
    spinner.style.display = 'none';
    
    titleEl.textContent = message;
    subtitleEl.textContent = '';
    
    if (type === 'success') {
        titleEl.style.color = '#10b981';
    } else if (type === 'error') {
        titleEl.style.color = '#ef4444';
    } else if (type === 'warning') {
        titleEl.style.color = '#f59e0b';
    }
    
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
        // Reset styles
        setTimeout(() => {
            spinner.style.display = 'block';
            titleEl.style.color = '#e0e0e0';
        }, 300);
    }, 2500);
}
