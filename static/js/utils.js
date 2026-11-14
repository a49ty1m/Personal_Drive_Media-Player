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


/**
 * Show VLC-style OSD (On-Screen Display) notification
 * Displays floating message on video player
 * 
 * @param {string} icon - Icon emoji (e.g., '🎵', '💬', '🔊')
 * @param {string} text - Text to display (e.g., 'Audio: English')
 */
function showOSD(icon, text) {
    const osdEl = document.getElementById('vlc-osd');
    if (!osdEl) return;
    
    const osdIcon = osdEl.querySelector('.osd-icon');
    const osdText = osdEl.querySelector('.osd-text');
    if (!osdIcon || !osdText) return;
    
    // Clear any existing timer
    if (window.osdTimer) {
        clearTimeout(window.osdTimer);
        window.osdTimer = null;
    }
    
    // Set content
    osdIcon.textContent = icon;
    osdText.textContent = text;
    
    // Show with animation
    osdEl.classList.remove('osd-fade');
    osdEl.classList.add('osd-visible');
    
    // Auto-hide after 1.2 seconds
    window.osdTimer = setTimeout(function() {
        osdEl.classList.add('osd-fade');
        setTimeout(function() {
            osdEl.classList.remove('osd-visible', 'osd-fade');
        }, 500);
    }, 1200);
}

// Expose globally for all scripts
window.showOSD = showOSD;
