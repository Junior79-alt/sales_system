// =========================================================
// SHARED UTILITIES — Tumia kwenye dashboards zote
// =========================================================

// ✅ Toast notification
function showToast(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 14px 24px;
        border-radius: 8px;
        color: white;
        font-weight: 600;
        font-size: 14px;
        z-index: 9999;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        animation: slideIn 0.3s ease;
        max-width: 400px;
        background: ${type === 'success' ? '#2e7d32' : type === 'error' ? '#d32f2f' : type === 'warning' ? '#ff9800' : '#1a237e'};
    `;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ✅ Loading spinner
function showLoading(elementId) {
    const el = document.getElementById(elementId);
    if (el) el.innerHTML = '<div style="text-align:center; padding:40px;"><div class="spinner"></div><p style="margin-top:15px; color:#666;">Inapakia...</p></div>';
}

// ✅ Escape HTML (XSS protection)
function escapeHtml(s) {
    if (s === null || s === undefined) return '';
    return String(s).replace(/[&<>"']/g, c => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}

// ✅ Format numbers (Tanzania)
function fmt(n) {
    return (n || 0).toLocaleString('sw-TZ');
}

// ✅ API fetch with error handling
async function apiFetch(path, options = {}) {
    const token = localStorage.getItem('token');
    const res = await fetch(`${window.location.origin}${path}`, {
        ...options,
        headers: {
            'Authorization': 'Bearer ' + token,
            ...(options.headers || {}),
        },
    });
    if (res.status === 401) {
        localStorage.clear();
        window.location.href = 'login.html';
        return null;
    }
    return res;
}

// ✅ Export table to CSV
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) {
        showToast('Table not found', 'error');
        return;
    }
    const rows = Array.from(table.querySelectorAll('tr'));
    const csv = rows.map(row =>
        Array.from(row.querySelectorAll('td, th'))
            .map(cell => `"${cell.textContent.trim().replace(/"/g, '""')}"`)
            .join(',')
    ).join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename + '.csv';
    a.click();
    URL.revokeObjectURL(url);
    showToast('CSV exported!', 'success');
}

// ✅ Search/Filter table
function filterTable(inputId, tableId) {
    const query = document.getElementById(inputId).value.toLowerCase();
    const rows = document.querySelectorAll(`#${tableId} tbody tr`);
    rows.forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(query) ? '' : 'none';
    });
}

// ✅ Dark mode toggle
function initTheme() {
    const saved = localStorage.getItem('theme');
    if (saved === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
    }
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    // Update button icon
    const btn = document.getElementById('themeBtn');
    if (btn) btn.textContent = next === 'dark' ? '☀️' : '🌙';
}

// ✅ Logout
function logout() {
    localStorage.clear();
    window.location.href = 'login.html';
}

// Init on load
initTheme();

// Update theme button on load
document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('themeBtn');
    if (btn) {
        const current = document.documentElement.getAttribute('data-theme');
        btn.textContent = current === 'dark' ? '☀️' : '🌙';
    }
});