// ContextKeep V1.0 WebUI - Main JavaScript

let memories = [];
let currentKey = null;
let currentView = 'grid';

// Load memories on page load
document.addEventListener('DOMContentLoaded', () => {
    loadMemories();
    setupEventListeners();
});

function setupEventListeners() {
    // Search
    document.getElementById('searchInput').addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        filterMemories(query);
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
        if (e.target.classList.contains('modal')) {
            closeAllModals();
        }
    });

    // Save new memory button
    document.getElementById('saveNewBtn').addEventListener('click', saveNewMemory);

    // Save edit button
    document.getElementById('saveEditBtn').addEventListener('click', saveEdit);

    // Confirm delete button
    document.getElementById('confirmDeleteBtn').addEventListener('click', confirmDelete);
}

function switchView(view) {
    currentView = view;

    // Update button states
    document.querySelectorAll('.view-controls .btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`${view}ViewBtn`).classList.add('active');

    // Show/hide containers
    const gridContainer = document.getElementById('memoriesContainer');
    const calendarContainer = document.getElementById('calendarContainer');

    if (view === 'calendar') {
        gridContainer.style.display = 'none';
        calendarContainer.style.display = 'grid';
        renderCalendar();
    } else {
        gridContainer.style.display = view === 'grid' ? 'grid' : 'block';
        calendarContainer.style.display = 'none';
        gridContainer.className = view === 'grid' ? 'memories-grid' : 'memories-list';
        renderMemories(memories);
    }
}

async function loadMemories() {
    try {
        const response = await fetch('/api/memories');
        const data = await response.json();

        if (data.success) {
            memories = data.memories;
            renderMemories(memories);
        }
    } catch (error) {
        console.error('Error loading memories:', error);
    }
}

function renderMemories(memoriesToRender) {
    const container = document.getElementById('memoriesContainer');

    if (memoriesToRender.length === 0) {
        container.innerHTML = '<p class="loading">No memories found.</p>';
        return;
    }

    container.innerHTML = memoriesToRender.map(mem => `
        <div class="memory-card">
            <h3>${escapeHtml(mem.title || mem.key)}</h3>
            <p class="meta">Key: ${escapeHtml(mem.key)}</p>
            <p class="meta">Updated: ${formatTimestamp(mem.updated_at)}</p>
            <p class="snippet">${escapeHtml(mem.snippet)}</p>
            <div class="card-actions">
                <button class="btn btn-primary" onclick="viewMemory('${escapeHtml(mem.key)}')">View</button>
                <button class="btn btn-secondary" onclick="editMemory('${escapeHtml(mem.key)}')">Edit</button>
                <button class="btn btn-danger" onclick="deleteMemory('${escapeHtml(mem.key)}')">Delete</button>
            </div>
        </div>
    `).join('');
}

function renderCalendar() {
    const calendarGrid = document.getElementById('calendarGrid');
    const calendarList = document.getElementById('calendarList');

    // Group memories by date
    const memoriesByDate = {};
    memories.forEach(mem => {
        const date = new Date(mem.updated_at).toDateString();
        if (!memoriesByDate[date]) {
            memoriesByDate[date] = [];
        }
        memoriesByDate[date].push(mem);
    });

    // Get current month days
    const today = new Date();
    const year = today.getFullYear();
    const month = today.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();

    // Render calendar grid
    let calendarHTML = '';
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    dayNames.forEach(day => {
        calendarHTML += `<div class="calendar-day-header">${day}</div>`;
    });

    const startingDayOfWeek = firstDay.getDay();
    for (let i = 0; i < startingDayOfWeek; i++) {
        calendarHTML += '<div class="calendar-day"></div>';
    }

    for (let day = 1; day <= daysInMonth; day++) {
        const date = new Date(year, month, day);
        const dateStr = date.toDateString();
        const dayMemories = memoriesByDate[dateStr] || [];

        calendarHTML += `
            <div class="calendar-day">
                <div class="calendar-day-header">${day}</div>
                ${dayMemories.map(m => `
                    <div class="calendar-memory" onclick="viewMemory('${escapeHtml(m.key)}')">${escapeHtml(m.title || m.key)}</div>
                `).join('')}
            </div>
        `;
    }

    calendarGrid.innerHTML = calendarHTML;

    // Render list view (sorted by date)
    const sortedDates = Object.keys(memoriesByDate).sort((a, b) => new Date(b) - new Date(a));
    let listHTML = '<h3>Recent Memories</h3>';
    sortedDates.forEach(date => {
        memoriesByDate[date].forEach(mem => {
            listHTML += `
                <div class="calendar-list-item" onclick="viewMemory('${escapeHtml(mem.key)}')">
                    <h4>${escapeHtml(mem.title || mem.key)}</h4>
                    <p>${formatTimestamp(mem.updated_at)}</p>
                </div>
            `;
        });
    });

    calendarList.innerHTML = listHTML;
}

function filterMemories(query) {
    if (!query) {
        renderMemories(memories);
        return;
    }

    const filtered = memories.filter(mem =>
        mem.key.toLowerCase().includes(query) ||
        (mem.title && mem.title.toLowerCase().includes(query)) ||
        mem.content.toLowerCase().includes(query)
    );

    renderMemories(filtered);
}

function openNewMemoryModal() {
    document.getElementById('newKey').value = '';
    document.getElementById('newTitle').value = '';
    document.getElementById('newContent').value = '';
    document.getElementById('newMemoryModal').style.display = 'block';
}

async function saveNewMemory() {
    const key = document.getElementById('newKey').value.trim();
    const title = document.getElementById('newTitle').value.trim();
    const content = document.getElementById('newContent').value.trim();

    if (!key) {
        alert('Memory key is required');
        return;
    }

    try {
        const response = await fetch('/api/memories', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                key: key,
                title: title,
                content: content,
                tags: []
            })
        });

        const data = await response.json();

        if (data.success) {
            closeAllModals();
            loadMemories();
        } else {
            alert('Error creating memory: ' + data.error);
        }
    } catch (error) {
        console.error('Error creating memory:', error);
        alert('Error creating memory');
    }
}

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

function editMemory(key) {
    const mem = memories.find(m => m.key === key);
    if (!mem) return;

    currentKey = key;

    // Strip auto-appended logs for editing
    let content = mem.content;
    const logPattern = /\n\n---\n\*\*.+\*\*.*$/g;
    content = content.replace(logPattern, '').trim();

    document.getElementById('editTitle').value = mem.title || mem.key;
    document.getElementById('editContent').value = content;

    document.getElementById('editModal').style.display = 'block';
}

async function saveEdit() {
    if (!currentKey) return;

    const title = document.getElementById('editTitle').value;
    const content = document.getElementById('editContent').value;

    try {
        const response = await fetch(`/api/memories/${encodeURIComponent(currentKey)}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: title,
                content: content,
                tags: [],
                action: 'Manual Edit via WebUI'
            })
        });

        const data = await response.json();

        if (data.success) {
            closeAllModals();
            loadMemories();
        } else {
            alert('Error saving memory: ' + data.error);
        }
    } catch (error) {
        console.error('Error saving memory:', error);
        alert('Error saving memory');
    }
}

function deleteMemory(key) {
    currentKey = key;
    const mem = memories.find(m => m.key === key);

    document.getElementById('deleteTitle').textContent = mem.title || mem.key;
    document.getElementById('deleteModal').style.display = 'block';
}

async function confirmDelete() {
    if (!currentKey) return;

    try {
        const response = await fetch(`/api/memories/${encodeURIComponent(currentKey)}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            closeAllModals();
            loadMemories();
        } else {
            alert('Error deleting memory: ' + data.error);
        }
    } catch (error) {
        console.error('Error deleting memory:', error);
        alert('Error deleting memory');
    }
}

function closeAllModals() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.style.display = 'none';
    });
    currentKey = null;
}

function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
