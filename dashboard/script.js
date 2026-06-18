const API_URL = window.location.origin;
let token = localStorage.getItem('token');

if (!token) {
    window.location.href = 'login.html';
}

// ========== USER INFO ==========
async function getUserInfo() {
    try {
        const res = await fetch(`${API_URL}/users/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed');
        const user = await res.json();
        document.getElementById('userName').textContent = user.email;
        document.getElementById('userRole').textContent = user.role || '';
        return user;
    } catch (e) { return null; }
}

// ========== LOGOUT ==========
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('userEmail');
    window.location.href = 'login.html';
}

// ========== FETCH SALES ==========
async function fetchSales() {
    try {
        const res = await fetch(`${API_URL}/sales/`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed');
        return await res.json();
    } catch (e) { return []; }
}

// ========== DASHBOARD ==========
async function loadDashboard() {
    const sales = await fetchSales();
    let totalAmount = 0, totalQty = 0;
    sales.forEach(s => { totalAmount += s.total_amount || 0; totalQty += s.quantity || 0; });

    document.getElementById('totalSales').textContent = totalAmount.toLocaleString() + ' TSh';
    document.getElementById('totalProducts').textContent = totalQty;
    document.getElementById('totalSalesCount').textContent = sales.length;
}

// ========== TABLE ==========
async function loadTable() {
    const sales = await fetchSales();
    const tbody = document.getElementById('salesTableBody');
    if (!sales || sales.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">Hakuna mauzo</td></tr>';
        return;
    }
    tbody.innerHTML = sales.map((s, i) => `
        <tr>
            <td>${i+1}</td>
            <td>${s.product_name || '-'}</td>
            <td>${s.quantity || 0}</td>
            <td>${(s.price || 0).toLocaleString()} TSh</td>
            <td><strong>${(s.total_amount || 0).toLocaleString()} TSh</strong></td>
            <td>${s.date ? new Date(s.date).toLocaleString('sw-TZ') : '-'}</td>
        </tr>
    `).join('');
}

// ========== RECENT ==========
async function loadRecent() {
    const sales = await fetchSales();
    const container = document.getElementById('recentSalesList');
    if (!sales || sales.length === 0) {
        container.innerHTML = '<p>Hakuna mauzo ya hivi karibuni</p>';
        return;
    }
    const recent = sales.slice(-5).reverse();
    container.innerHTML = recent.map(s => `
        <div class="recent-sale-item" style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #eee;">
            <span><strong>${s.product_name}</strong> (${s.quantity}x)</span>
            <span style="color:#1a237e;font-weight:bold;">${(s.total_amount || 0).toLocaleString()} TSh</span>
        </div>
    `).join('');
}

// ========== CHART ==========
async function loadChart() {
    const sales = await fetchSales();
    const ctx = document.getElementById('salesChart').getContext('2d');
    const byDate = {};
    sales.forEach(s => {
        const d = s.date ? s.date.split('T')[0] : 'Unknown';
        byDate[d] = (byDate[d] || 0) + (s.total_amount || 0);
    });
    const labels = Object.keys(byDate).sort();
    const data = labels.map(l => byDate[l]);

    if (window.salesChartInstance) window.salesChartInstance.destroy();
    window.salesChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels.length ? labels : ['Hakuna'],
            datasets: [{
                label: 'Mauzo (TSh)',
                data: data.length ? data : [0],
                backgroundColor: 'rgba(26,35,126,0.7)',
                borderColor: '#1a237e',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { callback: v => v.toLocaleString() + ' TSh' } } }
        }
    });
}

// ========== INIT ==========
getUserInfo();
loadDashboard();
loadTable();
loadRecent();
loadChart();

setInterval(() => {
    if (token) {
        loadDashboard();
        loadTable();
        loadRecent();
        loadChart();
    }
}, 30000);