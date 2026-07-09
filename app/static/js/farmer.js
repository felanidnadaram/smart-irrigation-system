const API_BASE = '';
let token = localStorage.getItem('farmer_token');
let currentFieldId = null;

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

function showAddFieldModal() {
    document.getElementById('fieldName').value = '';
    document.getElementById('fieldLocation').value = '';
    document.getElementById('fieldCrop').value = '';
    document.getElementById('fieldArea').value = '';
    document.getElementById('fieldNotes').value = '';
    document.getElementById('fieldIrrigation').value = '';
    document.getElementById('addFieldModal').classList.add('active');
}

function showEditFieldModal(field) {
    document.getElementById('editFieldId').value = field.id;
    document.getElementById('editFieldName').value = field.field_name;
    document.getElementById('editFieldLocation').value = field.location;
    document.getElementById('editFieldCrop').value = field.crop_type;
    document.getElementById('editFieldArea').value = field.area_hectares || '';
    document.getElementById('editFieldNotes').value = field.notes || '';
    document.getElementById('editFieldIrrigation').value = field.irrigation_schedule || '';
    document.getElementById('editFieldModal').classList.add('active');
}

async function loadDashboard() {
    try {
        const res = await fetch(`${API_BASE}/dashboard/farmer/overview`, { headers: getHeaders() });
        if (res.status === 401) { window.location.href = '/'; return; }
        const data = await res.json();

        document.getElementById('userName').textContent = data.user.full_name;
        document.getElementById('totalFields').textContent = data.total_fields;
        document.getElementById('activeFields').textContent = data.active_fields;
        document.getElementById('totalAlerts').textContent = data.total_alerts;

        renderFields(data.fields);
        await loadAlerts();
    } catch (e) {
        console.error(e);
    }
}

function renderFields(fields) {
    const grid = document.getElementById('fieldsGrid');
    if (!fields.length) {
        grid.innerHTML = '<div class="empty-state"><h3>هنوز مزرعه‌ای ثبت نشده</h3><p>اولین مزرعه خود را اضافه کنید</p></div>';
        return;
    }

    grid.innerHTML = fields.map(f => {
        const field = f.field;
        const reading = f.latest_reading;
        const moistureClass = reading && reading.soil_moisture < 30 ? 'alert' : '';
        const tempClass = reading && reading.temperature > 35 ? 'alert' : '';

        return `
        <div class="field-card">
            <div class="field-card-header">
                <h3>${field.field_name}</h3>
                ${f.alert_count > 0 ? `<span class="alert-badge">${f.alert_count} هشدار</span>` : ''}
            </div>
            <div class="field-card-body">
                <div class="info-row"><span class="info-label">موقعیت</span><span class="info-value">${field.location}</span></div>
                <div class="info-row"><span class="info-label">نوع محصول</span><span class="info-value">${field.crop_type}</span></div>
                ${field.area_hectares ? `<div class="info-row"><span class="info-label">مساحت</span><span class="info-value">${field.area_hectares} هکتار</span></div>` : ''}
                ${field.irrigation_schedule ? `<div class="info-row"><span class="info-label">برنامه آبیاری</span><span class="info-value">${field.irrigation_schedule}</span></div>` : ''}
                ${reading ? `
                <div class="sensor-values">
                    <div class="sensor-item ${moistureClass}"><div class="value">${reading.soil_moisture}%</div><div class="label">رطوبت خاک</div></div>
                    <div class="sensor-item ${tempClass}"><div class="value">${reading.temperature}°C</div><div class="label">دما</div></div>
                    <div class="sensor-item"><div class="value">${reading.humidity}%</div><div class="label">رطوبت هوا</div></div>
                    <div class="sensor-item"><div class="value">${reading.light_intensity} lx</div><div class="label">شدت نور</div></div>
                </div>` : '<p style="margin-top:10px;color:#999">داده سنسور موجود نیست</p>'}
                <div style="margin-top:15px;display:flex;gap:8px;flex-wrap:wrap">
                    <button class="btn btn-primary btn-sm" onclick="showFieldDetail('${field.id}', '${field.field_name}')">جزئیات</button>
                    <button class="btn btn-secondary btn-sm" onclick='showEditFieldModal(${JSON.stringify(field)})'>ویرایش</button>
                    <button class="btn btn-danger btn-sm" onclick="deleteField('${field.id}')">حذف</button>
                    <button class="btn btn-primary btn-sm" onclick="generateFieldData('${field.id}')">تولید داده</button>
                </div>
            </div>
        </div>`;
    }).join('');
}

async function loadAlerts() {
    try {
        const res = await fetch(`${API_BASE}/decisions/alerts/all`, { headers: getHeaders() });
        const decisions = await res.json();

        const tbody = document.getElementById('alertsBody');
        if (!decisions.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state">هشدار فعالی وجود ندارد</td></tr>';
            return;
        }

        tbody.innerHTML = decisions.map(d => `
            <tr>
                <td>${d.decision_type === 'irrigation' ? '💧 آبیاری' : d.decision_type === 'temperature_alert' ? '🌡️ دما' : d.decision_type === 'humidity_alert' ? '💨 رطوبت' : '☀️ نور'}</td>
                <td>${d.title}</td>
                <td>${d.description}</td>
                <td><span class="badge badge-${d.priority}">${d.priority === 'critical' ? 'بحرانی' : d.priority === 'high' ? 'بالا' : d.priority === 'medium' ? 'متوسط' : 'پایین'}</span></td>
                <td>${new Date(d.created_at).toLocaleDateString('fa-IR')}</td>
                <td><button class="btn btn-primary btn-sm" onclick="resolveDecision('${d.id}')">حل شد</button></td>
            </tr>
        `).join('');
    } catch (e) {
        console.error(e);
    }
}

async function createField(e) {
    e.preventDefault();
    try {
        const res = await fetch(`${API_BASE}/fields/`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({
                field_name: document.getElementById('fieldName').value,
                location: document.getElementById('fieldLocation').value,
                crop_type: document.getElementById('fieldCrop').value,
                area_hectares: parseFloat(document.getElementById('fieldArea').value) || null,
                notes: document.getElementById('fieldNotes').value || null,
                irrigation_schedule: document.getElementById('fieldIrrigation').value || null,
            })
        });
        if (res.ok) {
            showToast('مزرعه با موفقیت ایجاد شد');
            closeModal('addFieldModal');
            loadDashboard();
        } else {
            const err = await res.json();
            showToast(err.detail || 'خطا در ایجاد مزرعه', 'error');
        }
    } catch (e) {
        showToast('خطا در ارتباط با سرور', 'error');
    }
}

async function updateField(e) {
    e.preventDefault();
    const fieldId = document.getElementById('editFieldId').value;
    try {
        const res = await fetch(`${API_BASE}/fields/${fieldId}`, {
            method: 'PUT',
            headers: getHeaders(),
            body: JSON.stringify({
                field_name: document.getElementById('editFieldName').value,
                location: document.getElementById('editFieldLocation').value,
                crop_type: document.getElementById('editFieldCrop').value,
                area_hectares: parseFloat(document.getElementById('editFieldArea').value) || null,
                notes: document.getElementById('editFieldNotes').value || null,
                irrigation_schedule: document.getElementById('editFieldIrrigation').value || null,
            })
        });
        if (res.ok) {
            showToast('مزرعه با موفقیت بروزرسانی شد');
            closeModal('editFieldModal');
            loadDashboard();
        } else {
            const err = await res.json();
            showToast(err.detail || 'خطا در بروزرسانی', 'error');
        }
    } catch (e) {
        showToast('خطا در ارتباط با سرور', 'error');
    }
}

async function deleteField(fieldId) {
    if (!confirm('آیا از حذف این مزرعه مطمئن هستید؟')) return;
    try {
        const res = await fetch(`${API_BASE}/fields/${fieldId}`, {
            method: 'DELETE',
            headers: getHeaders()
        });
        if (res.ok) {
            showToast('مزرعه حذف شد');
            loadDashboard();
        } else {
            showToast('خطا در حذف مزرعه', 'error');
        }
    } catch (e) {
        showToast('خطا در ارتباط با سرور', 'error');
    }
}

async function generateFieldData(fieldId) {
    try {
        const res = await fetch(`${API_BASE}/sensors/${fieldId}/generate`, {
            method: 'POST',
            headers: getHeaders()
        });
        if (res.ok) {
            showToast('داده جدید تولید شد');
            loadDashboard();
        }
    } catch (e) {
        showToast('خطا در تولید داده', 'error');
    }
}

async function resolveDecision(decisionId) {
    try {
        await fetch(`${API_BASE}/decisions/${decisionId}/resolve`, {
            method: 'PUT',
            headers: getHeaders()
        });
        showToast('تصمیم حل شد');
        loadAlerts();
        loadDashboard();
    } catch (e) {
        showToast('خطا', 'error');
    }
}

async function showFieldDetail(fieldId, fieldName) {
    currentFieldId = fieldId;
    document.getElementById('detailFieldTitle').textContent = fieldName;
    const content = document.getElementById('fieldDetailContent');
    content.innerHTML = '<p>در حال بارگذاری...</p>';
    document.getElementById('fieldDetailModal').classList.add('active');

    try {
        const [latestRes, statsRes, predRes] = await Promise.all([
            fetch(`${API_BASE}/sensors/${fieldId}/latest`, { headers: getHeaders() }),
            fetch(`${API_BASE}/dashboard/farmer/field/${fieldId}/stats?hours=24`, { headers: getHeaders() }),
            fetch(`${API_BASE}/dashboard/farmer/field/${fieldId}/prediction`, { headers: getHeaders() }),
        ]);

        const latest = await latestRes.json();
        const stats = await statsRes.json();
        const pred = await predRes.json();

        content.innerHTML = `
            <h4 style="margin:15px 0 10px">آخرین داده سنسور</h4>
            <div class="sensor-values">
                <div class="sensor-item"><div class="value">${latest.soil_moisture || '-'}%</div><div class="label">رطوبت خاک</div></div>
                <div class="sensor-item"><div class="value">${latest.temperature || '-'}°C</div><div class="label">دما</div></div>
                <div class="sensor-item"><div class="value">${latest.humidity || '-'}%</div><div class="label">رطوبت هوا</div></div>
                <div class="sensor-item"><div class="value">${latest.light_intensity || '-'} lx</div><div class="label">شدت نور</div></div>
            </div>
            ${stats && stats.avg_soil_moisture ? `
            <h4 style="margin:15px 0 10px">میانگین ۲۴ ساعت اخیر</h4>
            <div class="sensor-values">
                <div class="sensor-item"><div class="value">${stats.avg_soil_moisture.toFixed(1)}%</div><div class="label">میانگین رطوبت</div></div>
                <div class="sensor-item"><div class="value">${stats.avg_temperature.toFixed(1)}°C</div><div class="label">میانگین دما</div></div>
                <div class="sensor-item"><div class="value">${stats.min_soil_moisture.toFixed(1)}-${stats.max_soil_moisture.toFixed(1)}%</div><div class="label">محدوده رطوبت</div></div>
                <div class="sensor-item"><div class="value">${stats.reading_count}</div><div class="label">تعداد خوانش‌ها</div></div>
            </div>` : ''}
            ${pred && pred.predicted_soil_moisture ? `
            <h4 style="margin:15px 0 10px">پیش‌بینی فردا</h4>
            <div class="sensor-values">
                <div class="sensor-item"><div class="value">${pred.predicted_soil_moisture}%</div><div class="label">رطوبت پیش‌بینی</div></div>
                <div class="sensor-item"><div class="value">${pred.predicted_temperature}°C</div><div class="label">دما پیش‌بینی</div></div>
                <div class="sensor-item"><div class="value">${(pred.confidence * 100).toFixed(0)}%</div><div class="label">اعتماد</div></div>
                <div class="sensor-item"><div class="value">${pred.trend}</div><div class="label">روند</div></div>
            </div>` : ''}
        `;
    } catch (e) {
        content.innerHTML = '<p>خطا در بارگذاری اطلاعات</p>';
    }
}

async function generateData() {
    if (!currentFieldId) return;
    try {
        const res = await fetch(`${API_BASE}/sensors/${currentFieldId}/generate`, {
            method: 'POST',
            headers: getHeaders()
        });
        if (res.ok) {
            showToast('داده جدید تولید شد');
            showFieldDetail(currentFieldId, document.getElementById('detailFieldTitle').textContent);
            loadDashboard();
        }
    } catch (e) {
        showToast('خطا', 'error');
    }
}

function logout() {
    localStorage.removeItem('farmer_token');
    localStorage.removeItem('farmer_role');
    window.location.href = '/';
}

document.addEventListener('DOMContentLoaded', () => {
    if (!token) { window.location.href = '/'; return; }
    loadDashboard();
});
