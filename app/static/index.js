// Frontend Application Logic for TCT_CRM E-commerce Database Previewer

// Global State
let currentTab = 'dashboard';
let theme = 'dark';
let activeSyncInterval = null;

// Pagination and Search State
const tableStates = {
    customers: { page: 1, limit: 10, search: '', total: 0 },
    orders: { page: 1, limit: 10, search: '', total: 0 },
    products: { page: 1, limit: 10, search: '', total: 0 },
    leads: { page: 1, limit: 10, search: '', total: 0 }
};

// Search Debounce Timers
const debounceTimers = {
    customers: null,
    orders: null,
    products: null,
    leads: null
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    checkDatabaseConnection();
    checkSyncStatusOnLoad();
    checkMarketingSyncStatusOnLoad();
    updateDashboardKPIs();
    loadDashboardCharts();
    
    // Periodically check connection status (every 10 seconds)
    setInterval(checkDatabaseConnection, 10000);
});

// Tab Switching Logic
function switchTab(tabId) {
    currentTab = tabId;
    
    // Update active nav button
    document.querySelectorAll('.nav-item').forEach(btn => {
        btn.classList.remove('active');
    });
    const activeBtn = document.getElementById(`nav-btn-${tabId}`);
    if (activeBtn) activeBtn.classList.add('active');
    
    // Update active tab panel
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active-tab');
    });
    const activeTab = document.getElementById(`tab-${tabId}`);
    if (activeTab) activeTab.classList.add('active-tab');
    
    // Fetch data if entering list tabs
    if (['customers', 'orders', 'products', 'leads'].includes(tabId)) {
        fetchTableData(tabId);
    } else if (tabId === 'analytics') {
        initAnalyticsDates();
        loadAnalyticsData();
    } else if (tabId === 'dashboard') {
        updateDashboardKPIs();
        checkDatabaseConnection();
        loadDashboardCharts();
    } else if (tabId === 'marketing') {
        const iframe = document.getElementById('marketing-iframe');
        if (iframe) {
            iframe.src = iframe.src;
        }
    } else if (tabId === 'sankey') {
        const iframe = document.getElementById('sankey-iframe');
        if (iframe) {
            iframe.src = iframe.src;
        }
    }
}

// Dark/Light Theme Toggle
function toggleTheme() {
    const isDark = document.getElementById('theme-switch-checkbox').checked;
    if (isDark) {
        document.body.classList.remove('light-theme');
        document.body.classList.add('dark-theme');
        theme = 'dark';
    } else {
        document.body.classList.remove('dark-theme');
        document.body.classList.add('light-theme');
        theme = 'light';
    }
    
    // Redraw charts with new theme colors
    if (currentTab === 'dashboard') {
        loadDashboardCharts();
    } else if (currentTab === 'analytics') {
        loadAnalyticsData();
    }
}

// API: Check PostgreSQL Database Health
async function checkDatabaseConnection() {
    const dot = document.getElementById('db-status-dot');
    const text = document.getElementById('db-status-text');
    
    try {
        dot.className = "status-dot loading";
        text.innerText = "Checking...";
        
        const res = await fetch('/api/health');
        const data = await res.json();
        
        if (data.database_connected) {
            dot.className = "status-dot online";
            text.innerText = "PostgreSQL Connected";
            
            // Update Mini Table details in Dashboard
            document.getElementById('db-detail-status').innerHTML = '<span class="status-dot online" style="width:8px;height:8px;margin-right:6px;"></span> Connected';
        } else {
            dot.className = "status-dot offline";
            text.innerText = "DB Connection Error";
            document.getElementById('db-detail-status').innerHTML = '<span class="status-dot offline" style="width:8px;height:8px;margin-right:6px;"></span> Offline (Credential Error)';
        }
    } catch (e) {
        dot.className = "status-dot offline";
        text.innerText = "Server Unreachable";
        document.getElementById('db-detail-status').innerHTML = '<span class="status-dot offline" style="width:8px;height:8px;margin-right:6px;"></span> API Server Offline';
    }
    
    // Populate DB settings details from UI check
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        // Fallback placeholder values or parse details if provided
        document.getElementById('db-detail-host').innerText = "localhost (PostgreSQL 18)";
        document.getElementById('db-detail-name').innerText = "TCT_CRM";
        document.getElementById('db-detail-schema').innerText = "public";
    } catch (err) {}
}

// API: Update Dashboard KPI card counts
async function updateDashboardKPIs() {
    const entities = ['customers', 'orders', 'products', 'leads'];
    
    for (const entity of entities) {
        try {
            const res = await fetch(`/api/raw/${entity}?page=1&limit=1`);
            if (!res.ok) {
                const kpiElem = document.getElementById(`kpi-${entity}-count`);
                if (kpiElem) kpiElem.innerText = "-";
                continue;
            }
            const json = await res.json();
            const count = json.pagination.total;
            tableStates[entity].total = count;
            
            const kpiElem = document.getElementById(`kpi-${entity}-count`);
            if (kpiElem) {
                // Animate count update
                animateValue(kpiElem, parseInt(kpiElem.innerText) || 0, count, 800);
            }
        } catch (e) {
            console.error(`Failed to load KPI for ${entity}`, e);
        }
    }
}

// KPI Count Counter Animation Helper
function animateValue(obj, start, end, duration) {
    if (start === end) return;
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        obj.innerHTML = Math.floor(progress * (end - start) + start);
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

// Debounced Input Handler for Table Search
function debounceSearch(entity) {
    clearTimeout(debounceTimers[entity]);
    debounceTimers[entity] = setTimeout(() => {
        tableStates[entity].search = document.getElementById(`${entity}-search-input`).value;
        tableStates[entity].page = 1;
        fetchTableData(entity);
    }, 450);
}

// API: Fetch Paginated Table Data
async function fetchTableData(entity) {
    const state = tableStates[entity];
    const tbody = document.querySelector(`#${entity}-table tbody`);
    const paginationBox = document.getElementById(`${entity}-pagination`);
    
    tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; padding: 30px;">Loading data...</td></tr>`;
    
    try {
        const queryParams = new URLSearchParams({
            page: state.page,
            limit: state.limit,
            search: state.search
        });
        
        const res = await fetch(`/api/raw/${entity}?${queryParams.toString()}`);
        const result = await res.json();
        
        if (!res.ok) {
            throw new Error(result.message || `HTTP ${res.status} error`);
        }
        
        if (!result.data || result.data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; padding: 30px; color: var(--text-hint);">No records found. Perform a synchronization in the Sync Console.</td></tr>`;
            paginationBox.innerHTML = "";
            return;
        }
        
        tbody.innerHTML = "";
        
        // Render Rows depending on Entity
        result.data.forEach(item => {
            const tr = document.createElement('tr');
            
            if (entity === 'customers') {
                tr.innerHTML = `
                    <td><strong>#${item.Id}</strong></td>
                    <td>${escapeHTML(item.TenKhachHang || 'N/A')}</td>
                    <td>${escapeHTML(item.SoDiDong || '-')}</td>
                    <td>${escapeHTML(item.Email || '-')}</td>
                    <td>${escapeHTML(item.DiaChi || 'N/A')}</td>
                    <td>${item.NgayTao ? formatDate(item.NgayTao) : '-'}</td>
                `;
            } else if (entity === 'orders') {
                tr.innerHTML = `
                    <td><strong>#${item.Id}</strong></td>
                    <td>${escapeHTML(item.SoHopDong || '-')}</td>
                    <td>${escapeHTML(item.SoPO || '-')}</td>
                    <td>${item.PhiDonHang ? formatCurrency(item.PhiDonHang) : '-'}</td>
                    <td>${item.PhiConLai ? formatCurrency(item.PhiConLai) : '-'}</td>
                    <td>${item.NgayCapNhat ? formatDate(item.NgayCapNhat) : '-'}</td>
                `;
            } else if (entity === 'products') {
                tr.innerHTML = `
                    <td><strong>#${item.Id}</strong></td>
                    <td><code>${escapeHTML(item.SKU || 'N/A')}</code></td>
                    <td>${escapeHTML(item.TenSanPham || 'N/A')}</td>
                    <td>${item.GiaNhap ? formatCurrency(item.GiaNhap) : '-'}</td>
                    <td>${item.GiaBan ? formatCurrency(item.GiaBan) : '-'}</td>
                    <td><span class="btn btn-secondary" style="padding: 2px 8px; font-size:11px; cursor:default;">Brand #${item.ThuongHieuId}</span></td>
                `;
            } else if (entity === 'leads') {
                tr.innerHTML = `
                    <td><strong>#${item.Id}</strong></td>
                    <td>${escapeHTML(item.TenKhachHang || 'N/A')}</td>
                    <td>${escapeHTML(item.SoDienThoai || '-')}</td>
                    <td>${escapeHTML(item.Email || '-')}</td>
                    <td>${escapeHTML(item.DiaChi || 'N/A')}</td>
                    <td><span class="sync-badge ${getLeadStatusClass(item.TrangThai)}" style="font-size:11px; padding: 2px 8px;">${getLeadStatusText(item.TrangThai)}</span></td>
                `;
            }
            tbody.appendChild(tr);
        });
        
        // Render Pagination Controls
        const pag = result.pagination;
        state.total = pag.total;
        
        paginationBox.innerHTML = `
            <div>Showing ${Math.min((pag.page-1)*pag.limit+1, pag.total)} to ${Math.min(pag.page*pag.limit, pag.total)} of ${pag.total} records</div>
            <div class="pagination-pages">
                <button class="btn btn-secondary" ${pag.page <= 1 ? 'disabled' : ''} onclick="changePage('${entity}', ${pag.page - 1})">Previous</button>
                <span>Page ${pag.page} of ${pag.totalPages}</span>
                <button class="btn btn-secondary" ${pag.page >= pag.totalPages ? 'disabled' : ''} onclick="changePage('${entity}', ${pag.page + 1})">Next</button>
            </div>
        `;
        
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; padding: 30px; color: var(--error);">Error loading records from local API: ${e.message}</td></tr>`;
        paginationBox.innerHTML = "";
    }
}

// Page Changer
function changePage(entity, targetPage) {
    tableStates[entity].page = targetPage;
    fetchTableData(entity);
}

// Escaping HTML to prevent XSS
function escapeHTML(str) {
    return str.replace(/[&<>'"]/g, 
        tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
    );
}

// Utility: Format Date string
function formatDate(dateStr) {
    try {
        const d = new Date(dateStr);
        return d.toLocaleDateString('vi-VN') + ' ' + d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
    } catch(e) {
        return dateStr;
    }
}

// Utility: Format Currency Value
function formatCurrency(val) {
    if (val === null || val === undefined || isNaN(val)) return "0 ₫";
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val);
}

// =====================================================================
// DATA SYNCHRONIZATION LOGIC (SYNC CONSOLE)
// =====================================================================

async function startSync() {
    const apiKey = document.getElementById('sync-api-key-input').value.trim();
    if (!apiKey) {
        alert("Please enter a valid CRM API key.");
        return;
    }
    
    const startBtn = document.getElementById('start-sync-btn');
    startBtn.disabled = true;
    startBtn.innerText = "Syncing...";
    
    document.getElementById('sync-progress-box').style.display = "block";
    updateProgress(0, "Initiating database sync...");
    
    // Clear log console
    const consoleLogs = document.getElementById('console-logs-body');
    consoleLogs.innerHTML = `<p class="system-log">[SYSTEM] Sync started by user. Waiting for server response...</p>`;
    
    try {
        const res = await fetch('/api/sync/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: apiKey })
        });
        const data = await res.json();
        
        if (res.status === 200) {
            // Success, start polling status
            addLogToConsole("[SYSTEM] Background sync thread launched successfully. Polling progress...", "system-log");
            
            // Set polling interval every 2 seconds
            if (activeSyncInterval) clearInterval(activeSyncInterval);
            activeSyncInterval = setInterval(pollSyncStatus, 2000);
        } else {
            throw new Error(data.detail || "Server rejected request.");
        }
    } catch (e) {
        addLogToConsole(`[ERROR] Failed to launch sync: ${e.message}`, "error-log");
        startBtn.disabled = false;
        startBtn.innerText = "Start Synchronization";
    }
}

// Check if sync is already running on page load
async function checkSyncStatusOnLoad() {
    try {
        const res = await fetch('/api/sync/status');
        const data = await res.json();
        
        if (data.status === "syncing") {
            document.getElementById('sync-progress-box').style.display = "block";
            const startBtn = document.getElementById('start-sync-btn');
            startBtn.disabled = true;
            startBtn.innerText = "Syncing...";
            
            // Populate logs
            const consoleLogs = document.getElementById('console-logs-body');
            consoleLogs.innerHTML = "";
            data.logs.forEach(l => {
                const lineClass = l.includes("[ERROR]") ? "error-log" : (l.includes("completed") ? "success-log" : "");
                addLogToConsole(l, lineClass);
            });
            
            // Start polling
            if (activeSyncInterval) clearInterval(activeSyncInterval);
            activeSyncInterval = setInterval(pollSyncStatus, 2000);
        }
    } catch (e) {
        console.error("Failed to check sync status on load", e);
    }
}

// Poll status of running synchronization
async function pollSyncStatus() {
    try {
        const res = await fetch('/api/sync/status');
        const data = await res.json();
        
        const badge = document.getElementById('sync-badge');
        const badgeText = document.getElementById('sync-badge-text');
        
        // Update Logs Console
        const consoleLogs = document.getElementById('console-logs-body');
        consoleLogs.innerHTML = "";
        data.logs.forEach(l => {
            let lineClass = "";
            if (l.includes("failed") || l.includes("HTTP")) lineClass = "error-log";
            else if (l.includes("completed") || l.includes("Successfully")) lineClass = "success-log";
            else if (l.includes("SYSTEM")) lineClass = "system-log";
            addLogToConsole(l, lineClass);
        });
        
        // Compute Progress percentage based on step names
        let percent = 0;
        let step = data.current_step || "Syncing...";
        
        if (data.status === "completed") {
            percent = 100;
            step = "Synchronization completed successfully.";
            badge.className = "sync-badge idle";
            badgeText.innerText = "Sync: Completed";
            
            // Stop polling
            clearInterval(activeSyncInterval);
            activeSyncInterval = null;
            
            // Re-enable button
            const startBtn = document.getElementById('start-sync-btn');
            startBtn.disabled = false;
            startBtn.innerText = "Start Synchronization";
            
            // Update counts in UI
            updateDashboardKPIs();
        } else if (data.status === "failed") {
            percent = 100;
            step = "Synchronization failed.";
            badge.className = "sync-badge failed";
            badgeText.innerText = "Sync: Failed";
            
            clearInterval(activeSyncInterval);
            activeSyncInterval = null;
            
            const startBtn = document.getElementById('start-sync-btn');
            startBtn.disabled = false;
            startBtn.innerText = "Start Synchronization";
        } else if (data.status === "syncing") {
            badge.className = "sync-badge syncing";
            badgeText.innerText = "Sync: In Progress";
            
            // Map percentage steps
            if (step.includes("products")) percent = 20;
            else if (step.includes("Customers")) percent = 50;
            else if (step.includes("Orders")) percent = 80;
            else if (step.includes("Leads")) percent = 95;
            else percent = 10;
        }
        
        updateProgress(percent, step);
    } catch (e) {
        console.error("Error polling sync status", e);
    }
}

// Console UI Log Writer Helper
function addLogToConsole(message, className) {
    const consoleLogs = document.getElementById('console-logs-body');
    const p = document.createElement('p');
    if (className) p.className = className;
    p.innerText = message;
    consoleLogs.appendChild(p);
    
    // Auto scroll to bottom
    consoleLogs.scrollTop = consoleLogs.scrollHeight;
}

// Progress Bar Helper
function updateProgress(percent, taskName) {
    document.getElementById('sync-progress-percent').innerText = `${percent}%`;
    document.getElementById('sync-progress-task').innerText = taskName;
    document.getElementById('sync-progress-bar-fill').style.width = `${percent}%`;
}

// =====================================================================
// ANALYTICS & GRAPH VIEW CHART BUILDERS
// =====================================================================

// Global Chart Instances
const chartInstances = {
    revenueTrend: null,
    funnelStages: null,
    salesRepRevenue: null,
    areaRevenue: null,
    customerGroupRevenue: null,
    leadSource: null,
    leadGroup: null,
    salesRepOpportunities: null,
    salesRepPipeline: null,
    pipelineTimeTrend: null,
    leadIndustry: null
};

// Initialize Date Filters if not set
function initAnalyticsDates() {
    const fromInput = document.getElementById('anal-date-from');
    const toInput = document.getElementById('anal-date-to');
    
    if (!fromInput.value || !toInput.value) {
        const today = new Date();
        const firstDayOfYear = new Date(today.getFullYear(), 0, 1);
        
        fromInput.value = firstDayOfYear.toISOString().split('T')[0];
        toInput.value = today.toISOString().split('T')[0];
    }
}

// Fetch stats and render/update all charts
async function loadAnalyticsData() {
    if (!window.Chart) {
        console.error("Chart.js is not loaded. Cannot render analytics graphs.");
        document.getElementById('anal-kpi-revenue').innerText = "0 ₫";
        document.getElementById('anal-kpi-avg-deal').innerText = "0 ₫";
        document.getElementById('anal-kpi-winrate').innerText = "0%";
        return;
    }
    const dateFrom = document.getElementById('anal-date-from').value;
    const dateTo = document.getElementById('anal-date-to').value;
    const groupBy = document.getElementById('anal-group-by').value;
    
    const queryParams = new URLSearchParams();
    if (dateFrom) queryParams.append('date_from', dateFrom);
    if (dateTo) queryParams.append('date_to', dateTo);
    
    const queryParamsWithGroup = new URLSearchParams(queryParams);
    if (groupBy) queryParamsWithGroup.append('group_by', groupBy);
    
    // Determine color scheme based on active theme
    const isDark = document.body.classList.contains('dark-theme');
    const textColor = isDark ? '#94a3b8' : '#475569';
    const gridColor = isDark ? '#334155' : '#cbd5e1';
    
    const chartDefaults = {
        color: textColor,
        borderColor: gridColor,
        font: { family: 'Inter, sans-serif' }
    };
    
    // Apply chart global defaults
    if (window.Chart) {
        Chart.defaults.color = textColor;
        Chart.defaults.borderColor = gridColor;
    }
    
    // 1. Fetch Revenue Trend over time
    try {
        const res = await fetch(`/api/orders/stats/revenue-by-time?${queryParamsWithGroup.toString()}`);
        const data = await res.json();
        
        let totalRevenueSum = 0;
        const labels = [];
        const revenues = [];
        const counts = [];
        
        if (res.ok && Array.isArray(data)) {
            data.forEach(item => {
                labels.push(item.period);
                revenues.push(item.total_revenue || 0);
                counts.push(item.order_count || 0);
                totalRevenueSum += (item.total_revenue || 0);
            });
        }
        
        // Update Revenue KPI
        document.getElementById('anal-kpi-revenue').innerText = formatCurrency(totalRevenueSum);
        
        // Render Chart 1: Revenue Trend
        renderRevenueTrendChart(labels, revenues, counts, chartDefaults);
    } catch (e) {
        console.error("Failed to load revenue trend stats", e);
    }
    
    // 2. Fetch Average Deal Size
    try {
        const res = await fetch(`/api/orders/stats/avg-deal-size?${queryParams.toString()}`);
        const data = await res.json();
        if (res.ok && data.avg_hours !== undefined) {
            // Reused avg_hours field for average order value in API schema
            document.getElementById('anal-kpi-avg-deal').innerText = formatCurrency(data.avg_hours);
        } else {
            document.getElementById('anal-kpi-avg-deal').innerText = "0 VND";
        }
    } catch(e) {
        document.getElementById('anal-kpi-avg-deal').innerText = "0 VND";
    }
    
    // 3. Fetch Win Rate
    try {
        const res = await fetch(`/api/conversions/stats/quotation-to-order?${queryParams.toString()}`);
        const data = await res.json();
        if (res.ok && data.conversion_rate !== undefined) {
            document.getElementById('anal-kpi-winrate').innerText = `${data.conversion_rate.toFixed(1)}%`;
        } else {
            document.getElementById('anal-kpi-winrate').innerText = "0%";
        }
    } catch (e) {
        document.getElementById('anal-kpi-winrate').innerText = "0%";
    }
    
    // 4. Fetch Funnel Stages (Opportunity Stages)
    try {
        const res = await fetch(`/api/opportunities/stats/by-stage?${queryParams.toString()}`);
        const data = await res.json();
        
        const labels = [];
        const counts = [];
        const values = [];
        
        if (res.ok && Array.isArray(data)) {
            data.forEach(item => {
                labels.push(item.stage_name);
                counts.push(item.count || 0);
                values.push(item.total_value || 0);
            });
        }
        
        renderFunnelStagesChart(labels, counts, values, chartDefaults);
    } catch (e) {
        console.error("Failed to load funnel stats", e);
    }
    
    // 5. Fetch Revenue by Sales Rep
    try {
        const res = await fetch(`/api/orders/stats/revenue-by-sales-rep?${queryParams.toString()}`);
        const data = await res.json();
        
        const reps = [];
        const revenues = [];
        
        if (res.ok && Array.isArray(data)) {
            data.forEach(item => {
                reps.push(item.rep_name || item.username || "Unknown");
                revenues.push(item.total_revenue || 0);
            });
        }
        
        renderSalesRepRevenueChart(reps, revenues, chartDefaults);
    } catch (e) {
        console.error("Failed to load sales rep revenue stats", e);
    }
    
    // 6. Fetch Revenue by Area
    try {
        const res = await fetch(`/api/orders/stats/revenue-by-area?${queryParams.toString()}`);
        const data = await res.json();
        
        const areas = [];
        const revenues = [];
        
        if (res.ok && Array.isArray(data)) {
            // Show top 8 areas, group the rest into others
            data.forEach((item, idx) => {
                if (idx < 7) {
                    areas.push(item.area || "Unknown");
                    revenues.push(item.total_revenue || 0);
                } else if (idx === 7) {
                    areas.push("Others");
                    revenues.push(item.total_revenue || 0);
                } else {
                    revenues[7] += (item.total_revenue || 0);
                }
            });
        }
        
        renderAreaRevenueChart(areas, revenues, chartDefaults);
    } catch (e) {
        console.error("Failed to load area revenue stats", e);
    }
    
    // 7. Fetch Revenue by Customer Group
    try {
        const res = await fetch(`/api/orders/stats/revenue-by-customer-group?${queryParams.toString()}`);
        const data = await res.json();
        
        const groups = [];
        const revenues = [];
        
        if (res.ok && Array.isArray(data)) {
            data.forEach(item => {
                groups.push(item.customer_group || "Unknown");
                revenues.push(item.total_revenue || 0);
            });
        }
        
        renderCustomerGroupRevenueChart(groups, revenues, chartDefaults);
    } catch (e) {
        console.error("Failed to load customer group revenue stats", e);
    }
    
    // 8. Fetch Lead by Source
    try {
        const res = await fetch(`/api/leads/stats/by-source?${queryParams.toString()}`);
        const data = await res.json();
        
        const sources = [];
        const counts = [];
        
        if (res.ok && data.success && Array.isArray(data.data)) {
            data.data.forEach(item => {
                sources.push(item.ten_nguon || "Unknown");
                counts.push(item.tong_lead || 0);
            });
        }
        
        renderLeadSourceChart(sources, counts, chartDefaults);
    } catch (e) {
        console.error("Failed to load lead source stats", e);
    }
    
    // 9. Fetch Lead by Group
    try {
        const res = await fetch(`/api/leads/stats/by-group?${queryParams.toString()}`);
        const data = await res.json();
        
        const groups = [];
        const counts = [];
        
        if (res.ok && Array.isArray(data)) {
            data.forEach(item => {
                groups.push(item.group || "Chưa phân loại");
                counts.push(item.count || 0);
            });
        }
        
        renderLeadGroupChart(groups, counts, chartDefaults);
    } catch (e) {
        console.error("Failed to load lead group stats", e);
    }
    
    // 9b. Fetch Lead by Industry
    try {
        const res = await fetch(`/api/leads/stats/by-industry?${queryParams.toString()}`);
        const data = await res.json();

        const industries = [];
        const counts = [];

        if (res.ok && Array.isArray(data)) {
            data.forEach(item => {
                industries.push(item.industry || 'Chưa phân loại');
                counts.push(item.count || 0);
            });
        }

        renderLeadIndustryChart(industries, counts, chartDefaults);
    } catch (e) {
        console.error("Failed to load lead industry stats", e);
    }

    // 10. Fetch Opportunity by Sales Rep
    try {
        const res = await fetch(`/api/opportunities/stats/by-sales-rep?${queryParams.toString()}`);
        const data = await res.json();
        
        const reps = [];
        const counts = [];
        const values = [];
        
        if (res.ok && Array.isArray(data)) {
            data.forEach(item => {
                reps.push(item.rep_name || item.username || "Unknown");
                counts.push(item.opportunity_count || 0);
                values.push(item.total_value || 0);
            });
        }
        
        renderSalesRepOpportunitiesChart(reps, counts, values, chartDefaults);
    } catch (e) {
        console.error("Failed to load sales rep opportunity stats", e);
    }
    
    // 11. Fetch Pipeline by Sales Rep
    try {
        const res = await fetch(`/api/opportunities/stats/pipeline-by-sales-rep?${queryParams.toString()}`);
        const data = await res.json();
        
        const reps = [];
        const pipelines = [];
        const counts = [];
        
        if (res.ok && Array.isArray(data)) {
            data.forEach(item => {
                reps.push(item.rep_name || item.username || "Unknown");
                pipelines.push(item.total_value || 0);
                counts.push(item.opportunity_count || 0);
            });
        }
        
        renderSalesRepPipelineChart(reps, pipelines, counts, chartDefaults);
    } catch (e) {
        console.error("Failed to load sales rep pipeline stats", e);
    }
    
    // 12. Fetch Pipeline Value Trend over time
    try {
        const res = await fetch(`/api/opportunities/stats/pipeline-by-time?${queryParamsWithGroup.toString()}`);
        const data = await res.json();
        
        const periods = [];
        const values = [];
        const counts = [];
        
        if (res.ok && Array.isArray(data)) {
            data.forEach(item => {
                periods.push(item.period);
                values.push(item.total_value || 0);
                counts.push(item.opportunity_count || 0);
            });
        }
        
        renderPipelineTimeTrendChart(periods, values, counts, chartDefaults);
    } catch (e) {
        console.error("Failed to load pipeline time trend stats", e);
    }
}

// Chart Helpers
function renderRevenueTrendChart(labels, revenues, counts, defaults) {
    const ctx = document.getElementById('chart-revenue-trend').getContext('2d');
    if (chartInstances.revenueTrend) chartInstances.revenueTrend.destroy();
    
    chartInstances.revenueTrend = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Doanh thu (VND)',
                    data: revenues,
                    borderColor: '#0ea5e9',
                    backgroundColor: 'rgba(14, 165, 233, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.3,
                    yAxisID: 'y-revenue'
                },
                {
                    label: 'Số lượng đơn hàng',
                    data: counts,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.2)',
                    borderWidth: 2,
                    type: 'bar',
                    borderRadius: 4,
                    yAxisID: 'y-count'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            if (context.datasetIndex === 0) {
                                return `Doanh thu: ${formatCurrency(context.raw)}`;
                            }
                            return `Đơn hàng: ${context.raw} đơn`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: defaults.borderColor },
                    ticks: { color: defaults.color }
                },
                'y-revenue': {
                    position: 'left',
                    grid: { color: defaults.borderColor },
                    ticks: {
                        color: defaults.color,
                        callback: function(value) {
                            if (value >= 1e9) return (value / 1e9) + ' B';
                            if (value >= 1e6) return (value / 1e6) + ' M';
                            return value;
                        }
                    }
                },
                'y-count': {
                    position: 'right',
                    grid: { drawOnChartArea: false },
                    ticks: { color: defaults.color, stepSize: 1 }
                }
            }
        }
    });
}

function renderFunnelStagesChart(labels, counts, values, defaults) {
    const ctx = document.getElementById('chart-funnel-stages').getContext('2d');
    if (chartInstances.funnelStages) chartInstances.funnelStages.destroy();
    
    chartInstances.funnelStages = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Số cơ hội',
                data: counts,
                backgroundColor: [
                    'rgba(14, 165, 233, 0.75)',  // Processing
                    'rgba(245, 158, 11, 0.75)',  // Quoted
                    'rgba(16, 185, 129, 0.75)',  // Won
                    'rgba(239, 68, 68, 0.75)'    // Lost
                ],
                borderColor: [
                    '#0ea5e9', '#f59e0b', '#10b981', '#ef4444'
                ],
                borderWidth: 1.5,
                borderRadius: 6
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        afterLabel: function(context) {
                            const val = values[context.dataIndex];
                            return `Giá trị cơ hội: ${formatCurrency(val)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: defaults.borderColor },
                    ticks: { color: defaults.color }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: defaults.color }
                }
            }
        }
    });
}

function renderSalesRepRevenueChart(reps, revenues, defaults) {
    const ctx = document.getElementById('chart-sales-rep-revenue').getContext('2d');
    if (chartInstances.salesRepRevenue) chartInstances.salesRepRevenue.destroy();
    
    chartInstances.salesRepRevenue = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: reps,
            datasets: [{
                data: revenues,
                backgroundColor: [
                    '#0ea5e9', '#10b981', '#f59e0b', '#ef4444', 
                    '#8b5cf6', '#ec4899', '#3b82f6', '#14b8a6'
                ],
                borderWidth: 2,
                borderColor: document.body.classList.contains('dark-theme') ? '#1e293b' : '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'right' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return ` ${context.label}: ${formatCurrency(context.raw)}`;
                        }
                    }
                }
            }
        }
    });
}

function renderAreaRevenueChart(areas, revenues, defaults) {
    const ctx = document.getElementById('chart-area-revenue').getContext('2d');
    if (chartInstances.areaRevenue) chartInstances.areaRevenue.destroy();
    
    chartInstances.areaRevenue = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: areas,
            datasets: [{
                label: 'Doanh thu (VND)',
                data: revenues,
                backgroundColor: 'rgba(139, 92, 246, 0.7)',
                borderColor: '#8b5cf6',
                borderWidth: 1.5,
                borderRadius: 6
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: {
                    grid: { color: defaults.borderColor },
                    ticks: { color: defaults.color }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: defaults.color }
                }
            }
        }
    });
}

function renderCustomerGroupRevenueChart(groups, revenues, defaults) {
    const ctx = document.getElementById('chart-customer-group-revenue').getContext('2d');
    if (chartInstances.customerGroupRevenue) chartInstances.customerGroupRevenue.destroy();
    
    chartInstances.customerGroupRevenue = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: groups,
            datasets: [{
                data: revenues,
                backgroundColor: [
                    '#3b82f6', '#ec4899', '#e2e8f0'
                ],
                borderWidth: 2,
                borderColor: document.body.classList.contains('dark-theme') ? '#1e293b' : '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'right' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return ` ${context.label}: ${formatCurrency(context.raw)}`;
                        }
                    }
                }
            }
        }
    });
}

function renderLeadSourceChart(sources, counts, defaults) {
    const ctx = document.getElementById('chart-lead-source').getContext('2d');
    if (chartInstances.leadSource) chartInstances.leadSource.destroy();
    
    chartInstances.leadSource = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: sources,
            datasets: [{
                data: counts,
                backgroundColor: [
                    '#3b82f6', '#10b981', '#f59e0b', '#ef4444', 
                    '#8b5cf6', '#ec4899', '#06b6d4', '#f43f5e',
                    '#14b8a6', '#64748b'
                ],
                borderWidth: 2,
                borderColor: document.body.classList.contains('dark-theme') ? '#1e293b' : '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'right' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return ` ${context.label}: ${context.raw} Lead`;
                        }
                    }
                }
            }
        }
    });
}

function renderLeadGroupChart(groups, counts, defaults) {
    const ctx = document.getElementById('chart-lead-group').getContext('2d');
    if (chartInstances.leadGroup) chartInstances.leadGroup.destroy();
    
    chartInstances.leadGroup = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: groups,
            datasets: [{
                data: counts,
                backgroundColor: [
                    '#10b981', '#ef4444', '#64748b'
                ],
                borderWidth: 2,
                borderColor: document.body.classList.contains('dark-theme') ? '#1e293b' : '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'right' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return ` ${context.label}: ${context.raw} Lead`;
                        }
                    }
                }
            }
        }
    });
}

function renderLeadIndustryChart(industries, counts, defaults) {
    const ctx = document.getElementById('chart-lead-industry').getContext('2d');
    if (chartInstances.leadIndustry) chartInstances.leadIndustry.destroy();

    chartInstances.leadIndustry = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: industries,
            datasets: [{
                label: 'Số Lead',
                data: counts,
                backgroundColor: 'rgba(20, 184, 166, 0.75)',
                borderColor: '#14b8a6',
                borderWidth: 1.5,
                borderRadius: 6
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.raw} Lead`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: defaults.borderColor },
                    ticks: { color: defaults.color, stepSize: 1 }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: defaults.color }
                }
            }
        }
    });
}

function renderSalesRepOpportunitiesChart(reps, counts, values, defaults) {
    const ctx = document.getElementById('chart-sales-rep-opportunities').getContext('2d');
    if (chartInstances.salesRepOpportunities) chartInstances.salesRepOpportunities.destroy();
    
    chartInstances.salesRepOpportunities = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: reps,
            datasets: [{
                label: 'Số cơ hội',
                data: counts,
                backgroundColor: 'rgba(59, 130, 246, 0.75)',
                borderColor: '#3b82f6',
                borderWidth: 1.5,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        afterLabel: function(context) {
                            const val = values[context.dataIndex];
                            return `Tổng giá trị: ${formatCurrency(val)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: defaults.color }
                },
                y: {
                    grid: { color: defaults.borderColor },
                    ticks: { color: defaults.color, stepSize: 1 }
                }
            }
        }
    });
}

function renderSalesRepPipelineChart(reps, pipelines, counts, defaults) {
    const ctx = document.getElementById('chart-sales-rep-pipeline').getContext('2d');
    if (chartInstances.salesRepPipeline) chartInstances.salesRepPipeline.destroy();
    
    chartInstances.salesRepPipeline = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: reps,
            datasets: [{
                label: 'Giá trị Pipeline (VND)',
                data: pipelines,
                backgroundColor: 'rgba(245, 158, 11, 0.75)',
                borderColor: '#f59e0b',
                borderWidth: 1.5,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Pipeline: ${formatCurrency(context.raw)}`;
                        },
                        afterLabel: function(context) {
                            const count = counts[context.dataIndex];
                            return `Số cơ hội: ${count} cơ hội`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: defaults.color }
                },
                y: {
                    grid: { color: defaults.borderColor },
                    ticks: {
                        color: defaults.color,
                        callback: function(value) {
                            if (value >= 1e9) return (value / 1e9) + ' B';
                            if (value >= 1e6) return (value / 1e6) + ' M';
                            return value;
                        }
                    }
                }
            }
        }
    });
}

function renderPipelineTimeTrendChart(labels, values, counts, defaults) {
    const ctx = document.getElementById('chart-pipeline-time-trend').getContext('2d');
    if (chartInstances.pipelineTimeTrend) chartInstances.pipelineTimeTrend.destroy();
    
    chartInstances.pipelineTimeTrend = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Giá trị Pipeline (VND)',
                    data: values,
                    borderColor: '#8b5cf6',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.3,
                    yAxisID: 'y-pipeline'
                },
                {
                    label: 'Số lượng cơ hội',
                    data: counts,
                    borderColor: '#0ea5e9',
                    backgroundColor: 'rgba(14, 165, 233, 0.2)',
                    borderWidth: 2,
                    type: 'bar',
                    borderRadius: 4,
                    yAxisID: 'y-count'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            if (context.datasetIndex === 0) {
                                return `Giá trị: ${formatCurrency(context.raw)}`;
                            }
                            return `Cơ hội: ${context.raw} cơ hội`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: defaults.borderColor },
                    ticks: { color: defaults.color }
                },
                'y-pipeline': {
                    position: 'left',
                    grid: { color: defaults.borderColor },
                    ticks: {
                        color: defaults.color,
                        callback: function(value) {
                            if (value >= 1e9) return (value / 1e9) + ' B';
                            if (value >= 1e6) return (value / 1e6) + ' M';
                            return value;
                        }
                    }
                },
                'y-count': {
                    position: 'right',
                    grid: { drawOnChartArea: false },
                    ticks: { color: defaults.color, stepSize: 1 }
                }
            }
        }
    });
}

// Helpers to map Lead Status codes to human-readable names and custom styles
function getLeadStatusText(statusCode) {
    const statusMap = {
        1: "New",
        2: "Quality",
        3: "Opty",
        4: "Quotation",
        5: "Process",
        6: "Finished",
        7: "Thất bại (New)",
        8: "Thất bại (Quality)"
    };
    return statusMap[statusCode] || `Status ${statusCode}`;
}

function getLeadStatusClass(statusCode) {
    const classMap = {
        1: "status-new",
        2: "status-quality",
        3: "status-opty",
        4: "status-quotation",
        5: "status-process",
        6: "status-finished",
        7: "status-failed-new",
        8: "status-failed-quality"
    };
    return classMap[statusCode] || "status-unknown";
}

// Marketing Synchronization Logic
let activeMarketingSyncInterval = null;

async function startMarketingSync() {
    const startBtn = document.getElementById('sync-marketing-btn');
    if (!startBtn) return;
    
    startBtn.disabled = true;
    startBtn.innerText = "Syncing...";
    
    try {
        const res = await fetch('/api/sync/marketing', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        
        if (res.status === 200) {
            // Polling interval every 2 seconds
            if (activeMarketingSyncInterval) clearInterval(activeMarketingSyncInterval);
            activeMarketingSyncInterval = setInterval(pollMarketingSyncStatus, 2000);
        } else {
            throw new Error(data.detail || "Server rejected request.");
        }
    } catch (e) {
        alert(`Failed to start marketing sync: ${e.message}`);
        startBtn.disabled = false;
        startBtn.innerText = "Sync Marketing Data";
    }
}

async function pollMarketingSyncStatus() {
    const startBtn = document.getElementById('sync-marketing-btn');
    if (!startBtn) return;
    
    try {
        const res = await fetch('/api/sync/marketing/status');
        const data = await res.json();
        
        if (data.status === "completed") {
            clearInterval(activeMarketingSyncInterval);
            activeMarketingSyncInterval = null;
            
            startBtn.disabled = false;
            startBtn.innerText = "Sync Marketing Data";
            
            // Reload iframe to show updated data
            const iframe = document.getElementById('marketing-iframe');
            if (iframe) {
                iframe.src = iframe.src;
            }
        } else if (data.status === "failed") {
            clearInterval(activeMarketingSyncInterval);
            activeMarketingSyncInterval = null;
            
            startBtn.disabled = false;
            startBtn.innerText = "Sync Marketing Data";
            alert(`Marketing sync failed: ${data.error || 'Unknown error'}`);
        } else if (data.status === "syncing") {
            startBtn.disabled = true;
            startBtn.innerText = "Syncing...";
        }
    } catch (e) {
        console.error("Error polling marketing sync status", e);
    }
}

async function checkMarketingSyncStatusOnLoad() {
    try {
        const res = await fetch('/api/sync/marketing/status');
        const data = await res.json();
        
        if (data.status === "syncing") {
            const startBtn = document.getElementById('sync-marketing-btn');
            if (startBtn) {
                startBtn.disabled = true;
                startBtn.innerText = "Syncing...";
            }
            if (activeMarketingSyncInterval) clearInterval(activeMarketingSyncInterval);
            activeMarketingSyncInterval = setInterval(pollMarketingSyncStatus, 2000);
        }
    } catch (e) {
        console.error("Failed to check marketing sync status on load", e);
    }
}

// Fetch and render product performance charts on Dashboard
let productRevenueChartInstance = null;
let productMarginChartInstance = null;

async function loadDashboardCharts() {
    if (!window.Chart) {
        console.error("Chart.js not loaded.");
        return;
    }
    
    try {
        const res = await fetch('/api/orders/stats/product-performance');
        if (!res.ok) {
            console.error("Failed to fetch product performance");
            return;
        }
        const data = await res.json();
        
        // Sort data by total_revenue descending and take top 8
        const topProducts = data.slice(0, 8);
        
        const labels = topProducts.map(p => p.sku || p.name);
        const revenues = topProducts.map(p => p.total_revenue);
        const margins = topProducts.map(p => p.margin_percent);
        const names = topProducts.map(p => p.name);
        
        const isDark = document.body.classList.contains('dark-theme');
        const textColor = isDark ? '#94a3b8' : '#475569';
        const gridColor = isDark ? '#334155' : '#cbd5e1';
        
        // 1. Revenue Bar Chart
        const ctxRev = document.getElementById('chart-product-revenue').getContext('2d');
        if (productRevenueChartInstance) productRevenueChartInstance.destroy();
        
        productRevenueChartInstance = new Chart(ctxRev, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Doanh thu (VND)',
                    data: revenues,
                    backgroundColor: 'rgba(14, 165, 233, 0.75)',
                    borderColor: '#0ea5e9',
                    borderWidth: 1.5,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            title: function(context) {
                                return names[context[0].dataIndex];
                            },
                            label: function(context) {
                                return `Doanh thu: ${formatCurrency(context.raw)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: textColor }
                    },
                    y: {
                        grid: { color: gridColor },
                        ticks: {
                            color: textColor,
                            callback: function(value) {
                                if (value >= 1e9) return (value / 1e9) + ' B';
                                if (value >= 1e6) return (value / 1e6) + ' M';
                                return value;
                            }
                        }
                    }
                }
            }
        });
        
        // 2. Margin Bar Chart
        const ctxMargin = document.getElementById('chart-product-margin').getContext('2d');
        if (productMarginChartInstance) productMarginChartInstance.destroy();
        
        productMarginChartInstance = new Chart(ctxMargin, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Biên lợi nhuận (%)',
                    data: margins,
                    backgroundColor: 'rgba(16, 185, 129, 0.75)',
                    borderColor: '#10b981',
                    borderWidth: 1.5,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            title: function(context) {
                                return names[context[0].dataIndex];
                            },
                            label: function(context) {
                                return `Biên lợi nhuận: ${context.raw}%`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: textColor }
                    },
                    y: {
                        grid: { color: gridColor },
                        ticks: {
                            color: textColor,
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
        
    } catch (e) {
        console.error("Error loading dashboard product charts", e);
    }
}
