/**
 * rename.js - File and folder renaming functionality
 */

let renameTargetPath = '';
let renameTargetName = '';
let renameTargetType = '';

// Show rename modal
function showRenameModal(path, name, type) {
    const modal = document.getElementById('renameModal');
    const input = document.getElementById('renameInput');
    const title = document.getElementById('renameModalTitle');
    
    if (modal && input && title) {
        renameTargetPath = path;
        renameTargetName = name;
        renameTargetType = type;
        
        // Update modal title
        title.textContent = `Rename ${type === 'folder' ? 'Folder' : 'File'}`;
        
        // Pre-fill input with current name
        input.value = name;
        
        // Select filename without extension for files
        modal.classList.add('show');
        input.focus();
        
        if (type === 'file') {
            const lastDot = name.lastIndexOf('.');
            if (lastDot > 0) {
                input.setSelectionRange(0, lastDot);
            } else {
                input.select();
            }
        } else {
            input.select();
        }
    }
}

// Close rename modal
function closeRenameModal() {
    const modal = document.getElementById('renameModal');
    if (modal) {
        modal.classList.remove('show');
    }
    renameTargetPath = '';
    renameTargetName = '';
    renameTargetType = '';
}

// Perform rename
async function performRename() {
    const input = document.getElementById('renameInput');
    const newName = input.value.trim();
    
    if (!newName) {
        showNotification('⚠ Please enter a name', 'warning');
        return;
    }
    
    if (newName === renameTargetName) {
        showNotification('⚠ New name is the same as the old name', 'warning');
        return;
    }
    
    // Validate name (no special characters)
    const invalidChars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|'];
    for (const char of invalidChars) {
        if (newName.includes(char)) {
            showNotification(`⚠ Name cannot contain: ${invalidChars.join(' ')}`, 'warning');
            return;
        }
    }
    
    if (newName.startsWith('.')) {
        showNotification('⚠ Name cannot start with a dot', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/api/rename', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                path: renameTargetPath,
                new_name: newName
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            closeRenameModal();
            
            // Show success message
            showNotification('✓ ' + (data.message || 'Renamed successfully'), 'success');
            
            // Reload page to show renamed item
            setTimeout(() => {
                window.location.reload();
            }, 800);
        } else {
            showNotification('✗ ' + (data.message || 'Failed to rename'), 'error');
        }
    } catch (error) {
        console.error('Error renaming:', error);
        showNotification('✗ Network error while renaming', 'error');
    }
}

// Handle Enter key in input field
document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('renameInput');
    if (input) {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                performRename();
            } else if (e.key === 'Escape') {
                closeRenameModal();
            }
        });
    }
    
    // Close modal when clicking outside
    const modal = document.getElementById('renameModal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeRenameModal();
            }
        });
    }
});
