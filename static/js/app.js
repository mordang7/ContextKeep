// ContextKeep V2.1 Atlas WebUI

let memories = [];
let categories = [];
let currentKey = null;
let currentCategoryId = null;
let currentCategoryName = '';
let currentView = 'grid';
let calendarYear = new Date().getFullYear();
let calendarMonth = new Date().getMonth();

const PAGE_LIMIT = 500;

document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    refreshAll();
});

function setupEventListeners() {
    document.getElementById('searchInput').addEventListener('input', debounce(handleSearch, 180));
    document.getElementById('gridViewBtn').addEventListener('click', () => switchView('grid'));
    document.getElementById('listViewBtn').addEventListener('click', () => switchView('list'));
    document.getElementById('calendarViewBtn').addEventListener('click', () => switchView('calendar'));
    document.getElementById('newMemoryBtn').addEventListener('click', openNewMemoryModal);
    document.getElementById('exportAllBtn').addEventListener('click', exportAll);
    document.getElementById('infoBtn').addEventListener('click', openInfoModal);
    document.getElementById('addCategoryBtn').addEventListener('click', () => openCategoryModal());
    document.getElementById('allCategoriesBtn').addEventListener('click', () => selectCategory(''));
    document.getElementById('saveNewBtn').addEventListener('click', saveNewMemory);
    document.getElementById('saveEditBtn').addEventListener('click', saveEdit);
    document.getElementById('confirmDeleteBtn').addEventListener('click', confirmDeleteMemory);
    document.getElementById('saveCategoryBtn').addEventListener('click', saveCategory);
    document.getElementById('confirmMergeBtn').addEventListener('click', confirmMergeCategory);
    document.getElementById('confirmDeleteCategoryBtn').addEventListener('click', confirmDeleteCategory);
    document.getElementById('calPrevBtn').addEventListener('click', prevMonth);
    document.getElementById('calNextBtn').addEventListener('click', nextMonth);

    document.querySelectorAll('[data-close]').forEach(btn => {
        btn.addEventListener('click', closeAllModals);
    });

    window.addEventListener('click', (event) => {
        if (event.target.classList.contains('modal')) closeAllModals();
    });

    document.getElementById('categoryList').addEventListener('click', handleCategoryListClick);
    document.getElementById('memoriesContainer').addEventListener('click', handleMemoryActionClick);
    document.getElementById('calendarGrid').addEventListener('click', handleCalendarClick);

    document.addEventListener('keydown', (event) => {
        if (event.ctrlKey && event.key.toLowerCase() === 'e') {
            event.preventDefault();
            exportAll();
        }
    });
}

async function apiJson(url, options = {}) {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!data.success) throw new Error(data.error || 'Request failed');
    return data;
}

async function refreshAll() {
    await Promise.all([loadCategories(), loadStats()]);
    await loadMemories();
}

async function loadCategories() {
    const data = await apiJson('/api/categories');
    categories = data.categories || [];
    renderCategories();
    renderCategorySelector('newCategorySelect', []);
}

async function loadStats() {
    const data = await apiJson('/api/stats');
    const stats = data.stats || {};
    document.getElementById('memoryCount').textContent = stats.total_memories || 0;
    document.getElementById('categoryCount').textContent = stats.total_categories || 0;
    document.getElementById('allCount').textContent = stats.total_memories || 0;
}

async function loadMemories() {
    const params = new URLSearchParams({ limit: String(PAGE_LIMIT) });
    if (currentCategoryName) params.set('category', currentCategoryName);
    const data = await apiJson(`/api/memories?${params.toString()}`);
    memories = data.memories || [];
    renderCurrentView();
    updatePanelTitle();
}

function renderCategories() {
    const list = document.getElementById('categoryList');
    list.innerHTML = categories.map(category => `
        <div class="category-item">
            <button class="category-row${currentCategoryName === category.name ? ' active' : ''}"
                    data-category="${escapeAttr(category.name)}"
                    data-id="${category.id}">
                <span class="category-icon">${escapeHtml(shortIcon(category.icon))}</span>
                <span class="category-name">${escapeHtml(category.name)}</span>
                <span class="category-count">${category.memory_count}</span>
            </button>
            <div class="category-actions">
                <button class="btn btn-secondary mini-btn" data-cat-action="edit" data-id="${category.id}">Edit</button>
                <button class="btn btn-secondary mini-btn" data-cat-action="merge" data-id="${category.id}">Merge</button>
                <button class="btn btn-danger mini-btn" data-cat-action="delete" data-id="${category.id}">Delete</button>
            </div>
        </div>
    `).join('');

    document.getElementById('allCategoriesBtn').classList.toggle('active', !currentCategoryName);
}

function handleCategoryListClick(event) {
    const actionButton = event.target.closest('[data-cat-action]');
    if (actionButton) {
        const category = findCategoryById(actionButton.dataset.id);
        if (!category) return;
        const action = actionButton.dataset.catAction;
        if (action === 'edit') openCategoryModal(category);
        if (action === 'merge') openMergeCategoryModal(category);
        if (action === 'delete') openDeleteCategoryModal(category);
        return;
    }

    const row = event.target.closest('.category-row');
    if (row) selectCategory(row.dataset.category || '');
}

async function selectCategory(name) {
    currentCategoryName = name || '';
    document.getElementById('searchInput').value = '';
    renderCategories();
    await loadMemories();
}

function updatePanelTitle() {
    const title = currentCategoryName || 'All Memories';
    document.getElementById('panelTitle').textContent = title;
    document.getElementById('panelSubtitle').textContent = currentCategoryName
        ? 'Filtered by category. Memories can belong to multiple categories.'
        : 'Browse, search, and organize long-term memory.';
    document.getElementById('memoryCount').textContent = memories.length;
}

function switchView(view) {
    currentView = view;
    document.querySelectorAll('.view-controls .btn-view').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`${view}ViewBtn`).classList.add('active');
    renderCurrentView();
}

function renderCurrentView() {
    const gridContainer = document.getElementById('memoriesContainer');
    const calendarContainer = document.getElementById('calendarContainer');
    if (currentView === 'calendar') {
        gridContainer.style.display = 'none';
        calendarContainer.style.display = 'flex';
        renderCalendar();
    } else {
        calendarContainer.style.display = 'none';
        gridContainer.style.display = currentView === 'grid' ? 'grid' : 'flex';
        gridContainer.className = currentView === 'grid' ? 'memories-grid' : 'memories-list';
        renderMemories(memories);
    }
}

function renderMemories(items) {
    const container = document.getElementById('memoriesContainer');
    if (!items.length) {
        container.innerHTML = '<p class="loading">No memories found.</p>';
        return;
    }

    container.innerHTML = items.map(memory => {
        const categoryHtml = (memory.categories || []).slice(0, 5)
            .map(category => `<span class="tag-chip">${escapeHtml(shortIcon(category.icon))} ${escapeHtml(category.name)}</span>`)
            .join('');
        const charBadge = memory.chars ? `<span class="char-badge">${formatChars(memory.chars)}</span>` : '';
        const snippet = memory.is_masked ? '[credential content hidden]' : (memory.snippet || '');
        return `
            <article class="memory-card">
                <h3>${escapeHtml(memory.title || memory.key)}</h3>
                <div class="card-key">${escapeHtml(memory.key)}</div>
                <p class="meta">${formatTimestamp(memory.updated_at)}</p>
                <p class="snippet">${escapeHtml(snippet)}</p>
                <div class="card-footer">
                    <div class="card-tags">${categoryHtml}</div>
                    ${charBadge}
                </div>
                <div class="card-actions">
                    <button class="btn btn-primary memory-action" data-action="view" data-key="${escapeAttr(memory.key)}">View</button>
                    <button class="btn btn-secondary memory-action" data-action="edit" data-key="${escapeAttr(memory.key)}">Edit</button>
                    <button class="btn btn-danger memory-action" data-action="delete" data-key="${escapeAttr(memory.key)}">Delete</button>
                </div>
            </article>
        `;
    }).join('');
}

function handleMemoryActionClick(event) {
    const button = event.target.closest('.memory-action');
    if (!button) return;
    const key = button.dataset.key;
    if (button.dataset.action === 'view') viewMemory(key);
    if (button.dataset.action === 'edit') editMemory(key);
    if (button.dataset.action === 'delete') deleteMemory(key);
}

async function handleSearch(event) {
    const query = event.target.value.trim();
    if (!query) {
        await loadMemories();
        return;
    }
    const params = new URLSearchParams({ q: query });
    if (currentCategoryName) params.set('category', currentCategoryName);
    const data = await apiJson(`/api/search?${params.toString()}`);
    memories = data.memories || [];
    renderCurrentView();
    document.getElementById('memoryCount').textContent = memories.length;
}

function openNewMemoryModal() {
    document.getElementById('newKey').value = '';
    document.getElementById('newTitle').value = '';
    document.getElementById('newContent').value = '';
    renderCategorySelector('newCategorySelect', currentCategoryName ? [currentCategoryName] : []);
    openModal('newMemoryModal');
}

async function saveNewMemory() {
    const key = document.getElementById('newKey').value.trim();
    const title = document.getElementById('newTitle').value.trim();
    const content = document.getElementById('newContent').value.trim();
    const selectedCategories = getSelectedCategories('newCategorySelect');
    if (!key) return alert('Memory key is required.');
    if (!content) return alert('Content is required.');
    if (!selectedCategories.length) return alert('Choose at least one category.');

    try {
        await apiJson('/api/memories', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key, title, content, categories: selectedCategories })
        });
        closeAllModals();
        await refreshAll();
    } catch (error) {
        alert(error.message);
    }
}

async function viewMemory(key, reveal = false) {
    try {
        currentKey = key;
        const data = await apiJson(`/api/memories/${encodeURIComponent(key)}${reveal ? '?reveal=1' : ''}`);
        const memory = data.memory;
        document.getElementById('viewTitle').textContent = memory.title || memory.key;
        document.getElementById('viewKey').textContent = memory.key;
        document.getElementById('viewTimestamp').textContent = formatTimestamp(memory.updated_at);
        document.getElementById('viewContent').textContent = memory.content;
        document.getElementById('viewCategories').innerHTML = (memory.categories || [])
            .map(category => `<span class="tag-chip">${escapeHtml(shortIcon(category.icon))} ${escapeHtml(category.name)}</span>`)
            .join('');
        renderHistory(memory.edit_history || []);

        const revealButton = document.getElementById('revealMemoryBtn');
        revealButton.style.display = memory.is_masked ? 'inline-flex' : 'none';
        revealButton.onclick = () => viewMemory(key, true);
        openModal('viewModal');
    } catch (error) {
        alert(error.message);
    }
}

async function editMemory(key) {
    try {
        currentKey = key;
        const data = await apiJson(`/api/memories/${encodeURIComponent(key)}?reveal=1`);
        const memory = data.memory;
        document.getElementById('editTitle').value = memory.title || memory.key;
        document.getElementById('editContent').value = memory.content || '';
        renderCategorySelector('editCategorySelect', (memory.categories || []).map(category => category.name));
        openModal('editModal');
    } catch (error) {
        alert(error.message);
    }
}

async function saveEdit() {
    if (!currentKey) return;
    const title = document.getElementById('editTitle').value.trim();
    const content = document.getElementById('editContent').value;
    const selectedCategories = getSelectedCategories('editCategorySelect');
    if (!selectedCategories.length) return alert('Choose at least one category.');

    try {
        await apiJson(`/api/memories/${encodeURIComponent(currentKey)}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, content, categories: selectedCategories })
        });
        closeAllModals();
        await refreshAll();
    } catch (error) {
        alert(error.message);
    }
}

function deleteMemory(key) {
    currentKey = key;
    const memory = memories.find(item => item.key === key);
    document.getElementById('deleteTitle').textContent = memory ? (memory.title || memory.key) : key;
    openModal('deleteModal');
}

async function confirmDeleteMemory() {
    if (!currentKey) return;
    try {
        await apiJson(`/api/memories/${encodeURIComponent(currentKey)}`, { method: 'DELETE' });
        closeAllModals();
        await refreshAll();
    } catch (error) {
        alert(error.message);
    }
}

function renderCategorySelector(containerId, selectedNames) {
    const selected = new Set((selectedNames || []).map(name => name.toLowerCase()));
    const container = document.getElementById(containerId);
    container.innerHTML = categories.map(category => {
        const checked = selected.has(category.name.toLowerCase()) ? 'checked' : '';
        return `
            <label class="category-option">
                <input type="checkbox" value="${escapeAttr(category.name)}" ${checked}>
                <span>${escapeHtml(shortIcon(category.icon))} ${escapeHtml(category.name)}</span>
            </label>
        `;
    }).join('');
}

function getSelectedCategories(containerId) {
    return Array.from(document.querySelectorAll(`#${containerId} input[type="checkbox"]:checked`))
        .map(input => input.value);
}

function openCategoryModal(category = null) {
    currentCategoryId = category ? category.id : null;
    document.getElementById('categoryModalTitle').textContent = category ? 'Edit Category' : 'Create Category';
    document.getElementById('categoryName').value = category ? category.name : '';
    document.getElementById('categoryIcon').value = category ? category.icon : 'folder';
    document.getElementById('categoryDescription').value = category ? category.description : '';
    openModal('categoryModal');
}

async function saveCategory() {
    const payload = {
        name: document.getElementById('categoryName').value.trim(),
        icon: document.getElementById('categoryIcon').value.trim() || 'folder',
        description: document.getElementById('categoryDescription').value.trim()
    };
    if (!payload.name) return alert('Category name is required.');

    try {
        if (currentCategoryId) {
            await apiJson(`/api/categories/${currentCategoryId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        } else {
            await apiJson('/api/categories', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        }
        closeAllModals();
        await refreshAll();
    } catch (error) {
        alert(error.message);
    }
}

function openMergeCategoryModal(category) {
    currentCategoryId = category.id;
    document.getElementById('mergeCategoryText').textContent =
        `Move memories from "${category.name}" into another category, then remove "${category.name}".`;
    fillCategorySelect('mergeTargetSelect', category.id);
    openModal('mergeCategoryModal');
}

async function confirmMergeCategory() {
    const targetId = document.getElementById('mergeTargetSelect').value;
    if (!targetId) return alert('Choose a target category.');
    try {
        await apiJson(`/api/categories/${currentCategoryId}/merge`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_id: Number(targetId) })
        });
        currentCategoryName = '';
        closeAllModals();
        await refreshAll();
    } catch (error) {
        alert(error.message);
    }
}

function openDeleteCategoryModal(category) {
    currentCategoryId = category.id;
    document.getElementById('deleteCategoryText').textContent = category.memory_count
        ? `"${category.name}" contains ${category.memory_count} memories. Choose where to reassign them before deleting.`
        : `"${category.name}" is empty and can be deleted.`;
    document.getElementById('reassignBlock').style.display = category.memory_count ? 'block' : 'none';
    fillCategorySelect('reassignTargetSelect', category.id);
    openModal('deleteCategoryModal');
}

async function confirmDeleteCategory() {
    const category = findCategoryById(currentCategoryId);
    const targetId = document.getElementById('reassignTargetSelect').value;
    if (category && category.memory_count && !targetId) return alert('Choose a reassignment category.');
    const query = targetId ? `?reassign_to=${encodeURIComponent(targetId)}` : '';
    try {
        await apiJson(`/api/categories/${currentCategoryId}${query}`, { method: 'DELETE' });
        currentCategoryName = '';
        closeAllModals();
        await refreshAll();
    } catch (error) {
        alert(error.message);
    }
}

function fillCategorySelect(selectId, excludeId) {
    const select = document.getElementById(selectId);
    select.innerHTML = categories
        .filter(category => Number(category.id) !== Number(excludeId))
        .map(category => `<option value="${category.id}">${escapeHtml(category.name)}</option>`)
        .join('');
}

async function openInfoModal() {
    try {
        const data = await apiJson('/api/info');
        document.getElementById('infoContent').textContent = JSON.stringify(data.info, null, 2);
        openModal('infoModal');
    } catch (error) {
        alert(error.message);
    }
}

function renderHistory(history) {
    const container = document.getElementById('viewHistory');
    if (!history.length) {
        container.innerHTML = '<div class="history-item">No edit history.</div>';
        return;
    }
    container.innerHTML = history.map(item => `
        <div class="history-item">
            <strong>${escapeHtml(item.action)}</strong> via ${escapeHtml(item.source)}
            <br>${escapeHtml(formatTimestamp(item.timestamp))}
        </div>
    `).join('');
}

function prevMonth() {
    calendarMonth -= 1;
    if (calendarMonth < 0) {
        calendarMonth = 11;
        calendarYear -= 1;
    }
    renderCalendar();
}

function nextMonth() {
    calendarMonth += 1;
    if (calendarMonth > 11) {
        calendarMonth = 0;
        calendarYear += 1;
    }
    renderCalendar();
}

function renderCalendar() {
    const calendarGrid = document.getElementById('calendarGrid');
    const label = document.getElementById('calMonthLabel');
    const today = new Date();
    const todayStr = today.toDateString();
    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'];
    label.textContent = `${monthNames[calendarMonth]} ${calendarYear}`;

    const byDate = {};
    memories.forEach(memory => {
        const date = new Date(memory.updated_at).toDateString();
        if (!byDate[date]) byDate[date] = [];
        byDate[date].push(memory);
    });

    const firstDay = new Date(calendarYear, calendarMonth, 1).getDay();
    const daysInMonth = new Date(calendarYear, calendarMonth + 1, 0).getDate();
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    let html = dayNames.map(day => `<div class="calendar-day-header">${day}</div>`).join('');
    for (let i = 0; i < firstDay; i += 1) html += '<div class="calendar-day empty"></div>';
    for (let day = 1; day <= daysInMonth; day += 1) {
        const date = new Date(calendarYear, calendarMonth, day);
        const dateStr = date.toDateString();
        const dayMemories = byDate[dateStr] || [];
        const memoriesHtml = dayMemories.slice(0, 4).map(memory =>
            `<div class="calendar-memory" data-key="${escapeAttr(memory.key)}">${escapeHtml(memory.title || memory.key)}</div>`
        ).join('');
        html += `
            <div class="calendar-day${dateStr === todayStr ? ' today' : ''}">
                <div class="calendar-day-num">${day}</div>
                ${memoriesHtml}
            </div>
        `;
    }
    calendarGrid.innerHTML = html;
}

function handleCalendarClick(event) {
    const item = event.target.closest('.calendar-memory');
    if (item) viewMemory(item.dataset.key);
}

async function exportAll() {
    const confirmed = confirm('Export includes full memory content, including credentials. Continue?');
    if (!confirmed) return;
    const button = document.getElementById('exportAllBtn');
    const originalText = button.textContent;
    button.textContent = 'Exporting...';
    button.disabled = true;
    try {
        const response = await fetch('/api/export');
        const blob = await response.blob();
        const disposition = response.headers.get('Content-Disposition') || '';
        const match = disposition.match(/filename=([^;]+)/);
        const filename = match ? match[1].trim() : `contextkeep_v2_backup_${new Date().toISOString().slice(0, 10)}.json`;
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        window.URL.revokeObjectURL(url);
        link.remove();
        button.textContent = 'Exported';
        setTimeout(() => { button.textContent = originalText; button.disabled = false; }, 1600);
    } catch (error) {
        alert('Export failed.');
        button.textContent = originalText;
        button.disabled = false;
    }
}

function openModal(id) {
    document.getElementById(id).style.display = 'block';
}

function closeAllModals() {
    document.querySelectorAll('.modal').forEach(modal => { modal.style.display = 'none'; });
    currentKey = null;
    currentCategoryId = null;
}

function findCategoryById(id) {
    return categories.find(category => Number(category.id) === Number(id));
}

function shortIcon(icon) {
    const value = String(icon || 'folder').trim();
    return value.length > 8 ? value.slice(0, 8) : value;
}

function formatChars(chars) {
    if (chars >= 1000) return `${(chars / 1000).toFixed(1)}k chars`;
    return `${chars} chars`;
}

function formatTimestamp(timestamp) {
    if (!timestamp) return '';
    return new Date(timestamp).toLocaleString();
}

function escapeHtml(value) {
    const div = document.createElement('div');
    div.textContent = String(value ?? '');
    return div.innerHTML;
}

function escapeAttr(value) {
    return escapeHtml(value)
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')
        .replace(/`/g, '&#96;');
}

function debounce(fn, delay) {
    let timer;
    return (...args) => {
        window.clearTimeout(timer);
        timer = window.setTimeout(() => fn(...args), delay);
    };
}
