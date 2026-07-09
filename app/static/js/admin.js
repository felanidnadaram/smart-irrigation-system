const API_BASE = '';
let token = localStorage.getItem('admin_token');

function getHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function closeModal(id) {
    document.getElementById(id).classList.remove('active');
}

function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('[id^="tab-"]').forEach(t => t.style.display = 'none');
    event.target.classList.add('active');
    document.getElementById(`tab-${tabName}`).style.display = 'block';

    if (tabName === 'overview') loadOverview();
    else if (tabName === 'users') loadUsers();
    else if (tabName === 'fields') loadAdminFields();
    else if (tabName === 'decisions') loadDecisions();
    else if (tabName === 'settings') loadThresholds();
}

function showAddUserModal() {
    document.getElementById('newUsername').value = '';
    document.getElementById('newPassword').value = '';
    document.getElementById('newFullName').value = '';
    document.getElementById('newPhone').value = '';
    document.getElementById('newRole').value = 'farmer';
    document.getElementById('addUserModal').classList.add('active');
}

function showAddFieldModal() {
    document.getElementById('adminFieldOwnerId').value = '';
    document.getElementById('adminFieldName').value = '';
    document.getElementById('adminFieldLocation').value = '';
    document.getElementById('adminFieldCrop').value = '';
    document.getElementById('adminFieldArea').value = '';
    document.getElementById('adminFieldNotes').value = '';
    document.getElementById('addFieldModal').classList.add('active');
}

async function loadOverview() {
    try {
        const res = await fetch(`${API_BASE}/dashboard/admin/stats`, { headers: getHeaders() });
        if (res.status === 401) { window.location.href = '/'; return; }
        const data = await res.json();

        document.getElementById('totalUsers').textContent = data.total_users;
        document.getElementById('totalFields').textContent = data.total_fields;
        document.getElementById('totalReadings').textContent = data.total_readings;
        document.getElementById('unresolvedDecisions').textContent = data.unresolved_decisions;

        if (data.sensor_averages_24h) {
            document.getElementById('avgMoisture').textContent = data.sensor_averages_24h.avg_soil_moisture + '%';
            document.getElementById('avgTemp').textContent = data.sensor_averages_24h.avg_temperature + '°C';
            document.getElementById('avgHumidity').textContent = data.sensor_averages_24h.avg_humidity + '%';
        }

        await loadEvents();
    } catch (e) { console.error(e); }
}

async function loadEvents() {
    try {
        const res = await fetch(`${API_BASE}/dashboard/admin/events`, { headers: getHeaders() });
        const events = await res.json();
        const tbody = document.getElementById('eventsBody');
        if (!events.length) {
            tbody.innerHTML = '<tr><td colspan="3" class="empty-state">رویدادی ثبت نشده</td></tr>';
            return;
        }
        tbody.innerHTML = events.slice(0, 20).map(e => `
            <tr>
                <td>${e.event_type === 'seed' ? '📊 بارگذاری' : e.event_type === 'system' ? '⚙️ سیستم' : '📝 ' + e.event_type}</td>
                <td>${e.message}</td>
                <td>${new Date(e.timestamp).toLocaleDateString('fa-IR')}</td>
            </tr>
        `).join('');
    } catch (e) { console.error(e); }
}

async function loadUsers() {
    try {
        const res = await fetch(`${API_BASE}/dashboard/admin/users`, { headers: getHeaders() });
        const users = await res.json();
        const tbody = document.getElementById('usersBody');
        tbody.innerHTML = users.map(u => `
            <tr>
                <td>${u.username}</td>
                <td>${u.full_name}</td>
                <td><span class="badge ${u.role === 'admin' ? 'badge-high' : 'badge-low'}">${u.role === 'admin' ? 'مدیر' : 'کشاورز'}</span></td>
                <td>${u.phone || '-'}</td>
                <td><span class="badge ${u.is_active ? 'badge-low' : 'badge-critical'}">${u.is_active ? 'فعال' : 'غیرفعال'}</span></td>
                <td>
                    <button class="btn btn-secondary btn-sm" onclick="toggleUserActive('${u.id}', ${!u.is_active})">${u.is_active ? 'غیرفعال' : 'فعال'} کردن</button>
                    <button class="btn btn-danger btn-sm" onclick="deleteUser('${u.id}')">حذف</button>
                </td>
            </tr>
        `).join('');
    } catch (e) { console.error(e); }
}

async function loadAdminFields() {
    try {
        const res = await fetch(`${API_BASE}/dashboard/admin/fields`, { headers: getHeaders() });
        const fields = await res.json();
        const tbody = document.getElementById('adminFieldsBody');
        tbody.innerHTML = fields.map(f => `
            <tr>
                <td>${f.field_name}</td>
                <td>${f.location}</td>
                <td>${f.crop_type}</td>
                <td>${f.area_hectares ? f.area_hectares + ' هکتار' : '-'}</td>
                <td>${f.owner_id}</td>
                <td><span class="badge ${f.is_active ? 'badge-low' : 'badge-critical'}">${f.is_active ? 'فعال' : 'غیرفعال'}</span></td>
                <td>
                    <button class="btn btn-primary btn-sm" onclick="generateAdminFieldData('${f.id}')">تولید داده</button>
                    <button class="btn btn-danger btn-sm" onclick="deleteAdminField('${f.id}')">حذف</button>
                </td>
            </tr>
        `).join('');
    } catch (e) { console.error(e); }
}

async function loadDecisions() {
    try {
        const res = await fetch(`${API_BASE}/dashboard/admin/decisions`, { headers: getHeaders() });
        const decisions = await res.json();
        const tbody = document.getElementById('decisionsBody');
        if (!decisions.length) {
            tbody.innerHTML = '<tr><td colspan="7" class="empty-state">تصمیمی ثبت نشده</td></tr>';
            return;
        }
        tbody.innerHTML = decisions.map(d => `
            <tr>
                <td>${d.decision_type === 'irrigation' ? '💧' : d.decision_type === 'temperature_alert' ? '🌡️' : '💨'}</td>
                <td>${d.title}</td>
                <td>${d.description}</td>
                <td><span class="badge badge-${d.priority}">${d.priority}</span></td>
                <td>${d.field_id}</td>
                <td><span class="badge ${d.is_resolved ? 'badge-low' : 'badge-high'}">${d.is_resolved ? 'حل شده' : 'فعال'}</span></td>
                <td>${new Date(d.created_at).toLocaleDateString('fa-IR')}</td>
            </tr>
        `).join('');
    } catch (e) { console.error(e); }
}

async function loadThresholds() {
    try {
        const res = await fetch(`${API_BASE}/dashboard/admin/thresholds`, { headers: getHeaders() });
        const th = await res.json();
        document.getElementById('thSoilMoistureLow').value = th.soil_moisture_low || '';
        document.getElementById('thSoilMoistureHigh').value = th.soil_moisture_high || '';
        document.getElementById('thTempHigh').value = th.temperature_high || '';
        document.getElementById('thTempLow').value = th.temperature_low || '';
        document.getElementById('thHumidityLow').value = th.humidity_low || '';
        document.getElementById('thHumidityHigh').value = th.humidity_high || '';
        document.getElementById('thLightHigh').value = th.light_intensity_high || '';
    } catch (e) { console.error(e); }
}

async function createUser(e) {
    e.preventDefault();
    try {
        const res = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: document.getElementById('newUsername').value,
                password: document.getElementById('newPassword').value,
                full_name: document.getElementById('newFullName').value,
                phone: document.getElementById('newPhone').value || null,
                role: document.getElementById('newRole').value,
            })
        });
        if (res.ok) {
            showToast('کاربر با موفقیت ایجاد شد');
            closeModal('addUserModal');
            loadUsers();
        } else {
            const err = await res.json();
            showToast(err.detail || 'خطا', 'error');
        }
    } catch (e) { showToast('خطا در ارتباط', 'error'); }
}

async function toggleUserActive(userId, active) {
    try {
        await fetch(`${API_BASE}/dashboard/admin/users/${userId}`, {
            method: 'PUT',
            headers: getHeaders(),
            body: JSON.stringify({ is_active: active })
        });
        showToast('وضعیت کاربر بروزرسانی شد');
        loadUsers();
    } catch (e) { showToast('خطا', 'error'); }
}

async function deleteUser(userId) {
    if (!confirm('آیا از حذف این کاربر مطمئن هستید؟')) return;
    try {
        const res = await fetch(`${API_BASE}/dashboard/admin/users/${userId}`, {
            method: 'DELETE',
            headers: getHeaders()
        });
        if (res.ok) { showToast('کاربر حذف شد'); loadUsers(); }
        else { const err = await res.json(); showToast(err.detail || 'خطا', 'error'); }
    } catch (e) { showToast('خطا', 'error'); }
}

async function createField(e) {
    e.preventDefault();
    try {
        const res = await fetch(`${API_BASE}/dashboard/admin/fields`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({
                owner_id: document.getElementById('adminFieldOwnerId').value,
                field_name: document.getElementById('adminFieldName').value,
                location: document.getElementById('adminFieldLocation').value,
                crop_type: document.getElementById('adminFieldCrop').value,
                area_hectares: parseFloat(document.getElementById('adminFieldArea').value) || null,
                notes: document.getElementById('adminFieldNotes').value || null,
            })
        });
        if (res.ok) {
            showToast('مزرعه ایجاد شد');
            closeModal('addFieldModal');
            loadAdminFields();
        } else {
            const err = await res.json();
            showToast(err.detail || 'خطا', 'error');
        }
    } catch (e) { showToast('خطا', 'error'); }
}

async function generateAdminFieldData(fieldId) {
    try {
        const res = await fetch(`${API_BASE}/sensors/${fieldId}/generate`, {
            method: 'POST',
            headers: getHeaders()
        });
        if (res.ok) { showToast('داده تولید شد'); loadAdminFields(); }
    } catch (e) { showToast('خطا', 'error'); }
}

async function deleteAdminField(fieldId) {
    if (!confirm('آیا از حذف این مزرعه مطمئن هستید؟')) return;
    try {
        const res = await fetch(`${API_BASE}/dashboard/admin/fields/${fieldId}`, {
            method: 'DELETE',
            headers: getHeaders()
        });
        if (res.ok) { showToast('مزرعه حذف شد'); loadAdminFields(); }
    } catch (e) { showToast('خطا', 'error'); }
}

async function updateThresholds(e) {
    e.preventDefault();
    try {
        const res = await fetch(`${API_BASE}/dashboard/admin/thresholds`, {
            method: 'PUT',
            headers: getHeaders(),
            body: JSON.stringify({
                soil_moisture_low: parseFloat(document.getElementById('thSoilMoistureLow').value) || null,
                soil_moisture_high: parseFloat(document.getElementById('thSoilMoistureHigh').value) || null,
                temperature_high: parseFloat(document.getElementById('thTempHigh').value) || null,
                temperature_low: parseFloat(document.getElementById('thTempLow').value) || null,
                humidity_low: parseFloat(document.getElementById('thHumidityLow').value) || null,
                humidity_high: parseFloat(document.getElementById('thHumidityHigh').value) || null,
                light_intensity_high: parseFloat(document.getElementById('thLightHigh').value) || null,
            })
        });
        if (res.ok) showToast('آستانه‌ها بروزرسانی شدند');
    } catch (e) { showToast('خطا', 'error'); }
}

async function generateAllData() {
    if (!confirm('داده جدید برای تمام مزارع تولید شود؟')) return;
    try {
        const res = await fetch(`${API_BASE}/dashboard/admin/generate-all`, {
            method: 'POST',
            headers: getHeaders()
        });
        if (res.ok) {
            const data = await res.json();
            showToast(data.message);
            loadOverview();
        }
    } catch (e) { showToast('خطا', 'error'); }
}

function logout() {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_role');
    window.location.href = '/';
}

document.addEventListener('DOMContentLoaded', () => {
    if (!token) { window.location.href = '/'; return; }
    loadOverview();
});
