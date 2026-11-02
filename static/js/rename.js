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
        modal.style.display = 'flex';
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
        modal.style.display = 'none';
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
        alert('Please enter a name');
        return;
    }
    
    if (newName === renameTargetName) {
        alert('New name is the same as the old name');
        return;
    }
    
    // Validate name (no special characters)
    const invalidChars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|'];
    for (const char of invalidChars) {
        if (newName.includes(char)) {
            alert(`Name cannot contain: ${invalidChars.join(' ')}`);
            return;
        }
    }
    
    if (newName.startsWith('.')) {
        alert('Name cannot start with a dot');
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
            alert(data.message || 'Renamed successfully');
            
            // Reload page to show renamed item
            setTimeout(() => {
                window.location.reload();
            }, 300);
        } else {
            alert(data.message || 'Failed to rename');
        }
    } catch (error) {
        console.error('Error renaming:', error);
        alert('Network error while renaming');
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
