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
        showNotification('Please enter a folder name', 'error');
        return;
    }
    
    // Validate folder name (no special characters that could cause issues)
    if (!/^[a-zA-Z0-9_\-\.\s]+$/.test(folderName)) {
        showNotification('Folder name contains invalid characters', 'error');
        return;
    }
    
    const currentPath = new URLSearchParams(window.location.search).get('path') || '/';
    
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
            showNotification(data.message || 'Folder created successfully', 'success');
            closeFolderModal();
            
            // Reload page to show new folder
            setTimeout(() => {
                window.location.reload();
            }, 500);
        } else {
            showNotification(data.error || 'Failed to create folder', 'error');
        }
    } catch (error) {
        console.error('Error creating folder:', error);
        showNotification('Network error while creating folder', 'error');
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
