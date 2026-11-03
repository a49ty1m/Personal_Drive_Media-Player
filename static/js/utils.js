/**
 * utils.js - Shared utility functions
 */

/**
 * Show notification (reuse ZIP notification element)
 * 
 * @param {string} message - The message to display
 * @param {string} type - Notification type: 'success', 'error', 'warning', or 'info'
 */
function showNotification(message, type) {
    const notification = document.getElementById('zipNotification');
    if (!notification) {
        alert(message); // Fallback
        return;
    }
    
    const titleEl = notification.querySelector('.zip-notification-title');
    const subtitleEl = notification.querySelector('.zip-notification-subtitle');
    const spinner = notification.querySelector('.zip-spinner');
    
    if (!titleEl || !subtitleEl || !spinner) {
        alert(message); // Fallback
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

// Make globally accessible
window.showNotification = showNotification;
