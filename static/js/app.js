// ContextKeep V1.3 Harbor WebUI — Main JavaScript

let memories = [];
let currentKey = null;
let currentView = 'grid';

// Calendar state
let calendarYear = new Date().getFullYear();
let calendarMonth = new Date().getMonth();

// ─── Init ───
document.addEventListener('DOMContentLoaded', () => {
    loadMemories();
    setupEventListeners();
});

// ─── Event Listeners ───
function setupEventListeners() {
    // Search
    document.getElementById('searchInput').addEventListener('input', (e) => {
        filterMemories(e.target.value.toLowerCase());
    });

    // View toggles
    document.getElementById('gridViewBtn').addEventListener('click', () => switchView('grid'));
    document.getElementById('listViewBtn').addEventListener('click', () => switchView('list'));
    document.getElementById('calendarViewBtn').addEventListener('click', () => switchView('calendar'));

    // New Memory button
    document.getElementById('newMemoryBtn').addEventListener('click', openNewMemoryModal);

    // Modal close buttons
    document.querySelectorAll('.close').forEach(btn => {
        btn.addEventListener('click', closeAllModals);
    });

    // Close modal on outside click
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) closeAllModals();
    });

    // Save buttons
    document.getElementById('saveNewBtn').addEventListener('click', saveNewMemory);
    document.getElementById('saveEditBtn').addEventListener('click', saveEdit);
    document.getElementById('confirmDeleteBtn').addEventListener('click', confirmDelete);

    // Export button
    document.getElementById('exportAllBtn').addEventListener('click', exportAll);

    // Keyboard shortcut: Ctrl+E for export
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'e') {
            e.preventDefault();
            exportAll();
        }
    });
}

// ─── View Switching ───
function switchView(view) {
    currentView = view;

    document.querySelectorAll('.view-controls .btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`${view}ViewBtn`).classList.add('active');

    const gridContainer = document.getElementById('memoriesContainer');
    const calendarContainer = document.getElementById('calendarContainer');

    if (view === 'calendar') {
        gridContainer.style.display = 'none';
        calendarContainer.style.display = 'flex';
        renderCalendar();
    } else {
        gridContainer.style.display = view === 'grid' ? 'grid' : 'block';
        calendarContainer.style.display = 'none';
        gridContainer.className = view === 'grid' ? 'memories-grid' : 'memories-list';
        renderMemories(memories);
    }
}

// ─── Load Memories ───
async function loadMemories() {
    try {
        const response = await fetch('/api/memories');
        const data = await response.json();
        if (data.success) {
            memories = data.memories;
            renderMemories(memories);
            updateMemoryCount(memories.length);
        }
    } catch (error) {
        console.error('Error loading memories:', error);
    }
}

function updateMemoryCount(count) {
    const el = document.getElementById('memoryCount');
    if (el) el.textContent = count;
}

// ─── Render Memory Cards ───
function renderMemories(memoriesToRender) {
    const container = document.getElementById('memoriesContainer');

    if (memoriesToRender.length === 0) {
        container.innerHTML = '<p class="loading">No memories found.</p>';
        return;
    }

    container.innerHTML = memoriesToRender.map(mem => {
        const tags = (mem.tags || []);
        const tagHTML = tags.length > 0
            ? tags.slice(0, 4).map(t => `<span class="tag-chip">${escapeHtml(t)}</span>`).join('')
            : '';
        const charCount = mem.chars ? formatChars(mem.chars) : '';
        const charBadge = charCount ? `<span class="char-badge">${charCount}</span>` : '';

        return `
        <div class="memory-card">
            <h3>${escapeHtml(mem.title || mem.key)}</h3>
            <div class="card-key">${escapeHtml(mem.key)}</div>
            <p class="meta">${formatTimestamp(mem.updated_at)}</p>
            <p class="snippet">${escapeHtml(mem.snippet || '')}</p>
            <div class="card-footer">
                <div class="card-tags">${tagHTML}</div>
                ${charBadge}
            </div>
            <div class="card-actions">
                <button class="btn btn-primary" onclick="viewMemory('${encodeKey(mem.key)}')">View</button>
                <button class="btn btn-secondary" onclick="editMemory('${encodeKey(mem.key)}')">Edit</button>
                <button class="btn btn-danger" onclick="deleteMemory('${encodeKey(mem.key)}')">Delete</button>
            </div>
        </div>`;
    }).join('');
}

function formatChars(chars) {
    if (chars >= 1000) return `${(chars / 1000).toFixed(1)}k chars`;
    return `${chars} chars`;
}

// ─── Calendar ───
function prevMonth() {
    calendarMonth--;
    if (calendarMonth < 0) { calendarMonth = 11; calendarYear--; }
    renderCalendar();
}

function nextMonth() {
    calendarMonth++;
    if (calendarMonth > 11) { calendarMonth = 0; calendarYear++; }
    renderCalendar();
}

function renderCalendar() {
    const calendarGrid = document.getElementById('calendarGrid');
    const calMonthLabel = document.getElementById('calMonthLabel');

    const today = new Date();
    const todayStr = today.toDateString();

    const year = calendarYear;
    const month = calendarMonth;

    // Update month label
    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'];
    calMonthLabel.textContent = `${monthNames[month]} ${year}`;

    // Group memories by date
    const memoriesByDate = {};
    memories.forEach(mem => {
        const date = new Date(mem.updated_at).toDateString();
        if (!memoriesByDate[date]) memoriesByDate[date] = [];
        memoriesByDate[date].push(mem);
    });

    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    // Day headers
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    let html = dayNames.map(d => `<div class="calendar-day-header">${d}</div>`).join('');

    // Empty cells before first day
    for (let i = 0; i < firstDay; i++) {
        html += '<div class="calendar-day empty"></div>';
    }

    // Day cells
    for (let day = 1; day <= daysInMonth; day++) {
        const date = new Date(year, month, day);
        const dateStr = date.toDateString();
        const isToday = dateStr === todayStr;
        const dayMemories = memoriesByDate[dateStr] || [];

        const memoriesHTML = dayMemories
            .slice(0, 4)
            .map(m => `<div class="calendar-memory" onclick="viewMemory('${encodeKey(m.key)}')">${escapeHtml(m.title || m.key)}</div>`)
            .join('');

        html += `
            <div class="calendar-day${isToday ? ' today' : ''}">
                <div class="calendar-day-num">${day}</div>
                ${memoriesHTML}
            </div>`;
    }

    calendarGrid.innerHTML = html;
}

// ─── Filter ───
function filterMemories(query) {
    if (!query) {
        renderMemories(memories);
        updateMemoryCount(memories.length);
        return;
    }
    const filtered = memories.filter(mem =>
        mem.key.toLowerCase().includes(query) ||
        (mem.title && mem.title.toLowerCase().includes(query)) ||
        mem.content.toLowerCase().includes(query)
    );
    renderMemories(filtered);
    updateMemoryCount(filtered.length);
}

// ─── New Memory Modal ───
function openNewMemoryModal() {
    document.getElementById('newKey').value = '';
    document.getElementById('newTitle').value = '';
    document.getElementById('newContent').value = '';
    document.getElementById('newMemoryModal').style.display = 'block';
}

// ─── Save New Memory ───
async function saveNewMemory() {
    const key = document.getElementById('newKey').value.trim();
    const title = document.getElementById('newTitle').value.trim();
    const content = document.getElementById('newContent').value.trim();

    if (!key) { alert('Memory key is required'); return; }
    if (!content) { alert('Content is required'); return; }

    try {
        const response = await fetch('/api/memories', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key, title, content, tags: [] })
        });
        const data = await response.json();
        if (data.success) { closeAllModals(); loadMemories(); }
        else alert('Error creating memory: ' + data.error);
    } catch (error) {
        console.error('Error creating memory:', error);
        alert('Error creating memory');
    }
}

// ─── View Memory ───
async function viewMemory(key) {
    try {
        const response = await fetch(`/api/memories/${encodeURIComponent(key)}`);
        const data = await response.json();
        if (data.success) {
            const mem = data.memory;
            document.getElementById('viewTitle').textContent = mem.title || mem.key;
            document.getElementById('viewKey').textContent = mem.key;
            document.getElementById('viewTimestamp').textContent = formatTimestamp(mem.updated_at);
            document.getElementById('viewContent').textContent = mem.content;
            document.getElementById('viewModal').style.display = 'block';
        }
    } catch (error) {
        console.error('Error viewing memory:', error);
    }
}

// ─── Edit Memory ───
function editMemory(key) {
    const mem = memories.find(m => m.key === key);
    if (!mem) return;
    currentKey = key;

    let content = mem.content;
    const logPattern = /\n\n---\n\*\*.+\*\*.*$/g;
    content = content.replace(logPattern, '').trim();

    document.getElementById('editTitle').value = mem.title || mem.key;
    document.getElementById('editContent').value = content;
    document.getElementById('editModal').style.display = 'block';
}

// ─── Save Edit ───
async function saveEdit() {
    if (!currentKey) return;
    const title = document.getElementById('editTitle').value;
    const content = document.getElementById('editContent').value;

    try {
        const response = await fetch(`/api/memories/${encodeURIComponent(currentKey)}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, content, tags: [], action: 'Manual Edit via WebUI' })
        });
        const data = await response.json();
        if (data.success) { closeAllModals(); loadMemories(); }
        else alert('Error saving memory: ' + data.error);
    } catch (error) {
        console.error('Error saving memory:', error);
        alert('Error saving memory');
    }
}

// ─── Delete Memory ───
function deleteMemory(key) {
    currentKey = key;
    const mem = memories.find(m => m.key === key);
    document.getElementById('deleteTitle').textContent = mem ? (mem.title || mem.key) : key;
    document.getElementById('deleteModal').style.display = 'block';
}

async function confirmDelete() {
    if (!currentKey) return;
    try {
        const response = await fetch(`/api/memories/${encodeURIComponent(currentKey)}`, { method: 'DELETE' });
        const data = await response.json();
        if (data.success) { closeAllModals(); loadMemories(); }
        else alert('Error deleting memory: ' + data.error);
    } catch (error) {
        console.error('Error deleting memory:', error);
        alert('Error deleting memory');
    }
}

// ─── Utilities ───
function closeAllModals() {
    document.querySelectorAll('.modal').forEach(m => m.style.display = 'none');
    currentKey = null;
}

function formatTimestamp(timestamp) {
    return new Date(timestamp).toLocaleString();
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

// Encode memory key safely for use in onclick attributes
function encodeKey(key) {
    return escapeHtml(key).replace(/'/g, '&#39;');
}

// ─── Export All ───
async function exportAll() {
    try {
        const btn = document.getElementById('exportAllBtn');
        const originalText = btn.textContent;
        btn.textContent = '⏳ Exporting...';
        btn.disabled = true;

        const response = await fetch('/api/export');
        const blob = await response.blob();

        // Extract filename from Content-Disposition header or generate one
        const disposition = response.headers.get('Content-Disposition');
        let filename = `contextkeep_backup_${new Date().toISOString().slice(0, 10)}.json`;
        if (disposition && disposition.includes('filename=')) {
            filename = disposition.split('filename=')[1].trim();
        }

        // Trigger download
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();

        btn.textContent = '✅ Exported!';
        setTimeout(() => {
            btn.textContent = originalText;
            btn.disabled = false;
        }, 2000);
    } catch (error) {
        console.error('Error exporting memories:', error);
        alert('Error exporting memories');
        const btn = document.getElementById('exportAllBtn');
        btn.textContent = '⬇ Export';
        btn.disabled = false;
    }
}
