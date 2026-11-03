/**
 * folder.js - Folder creation functionality
 */

// Show create folder modal
function showCreateFolderModal() {
    const modal = document.getElementById('folderModal');
    const input = document.getElementById('folderNameInput');
    
    if (modal && input) {
        input.value = '';
        modal.classList.add('show');
        input.focus();
    }
}

// Close create folder modal
function closeFolderModal() {
    const modal = document.getElementById('folderModal');
    if (modal) {
        modal.classList.remove('show');
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
