// campaign-detail.js - Скрипт для управления страницей кампании

let currentCampaignId = null;
let currentNmId = null;
let currentPhrases = [];
let campaignData = null;
let nmPhrasesMap = {}; // Хранилище минус-фраз для каждого товара
let statsPhrases = []; // Текущая статистика фраз
let currentPhraseToAdd = null; // Фраза для добавления в минус-фразы
let clustersData = { active: [], excluded: [] }; // Текущие кластеры
let selectedClusters = []; // Выбранные кластеры для добавления в минус
let currentApiToken = null; // Токен текущего пользователя

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', async function() {
    currentCampaignId = parseInt(document.getElementById('campaignId').textContent);
    // Сначала загружаем токен
    await loadApiToken();
    // Теперь загружаем кампанию с токеном
    loadCampaignData();
    initStatsDates();
});

// Загрузка API токена пользователя
async function loadApiToken() {
    try {
        const response = await fetch('/auth/token');
        const data = await response.json();
        if (response.ok && data.has_token) {
            currentApiToken = data.token;
            console.log('API токен загружен');
        } else {
            console.warn('API токен не найден');
        }
    } catch (error) {
        console.error('Error loading API token:', error);
    }
}

// Инициализация дат статистики (последние 7 дней)
function initStatsDates() {
    const today = new Date();
    const weekAgo = new Date(today);
    weekAgo.setDate(weekAgo.getDate() - 7);
    
    document.getElementById('statsFromDate').value = weekAgo.toISOString().split('T')[0];
    document.getElementById('statsToDate').value = today.toISOString().split('T')[0];
}

// Загрузка данных кампании
async function loadCampaignData() {
    showLoading(true);
    hideError();

    try {
        const headers = {};
        if (currentApiToken) {
            headers['X-API-Token'] = currentApiToken;
        }
        
        const response = await fetch(`/campaigns/adverts?ids=${currentCampaignId}`, { headers });
        if (!response.ok) {
            throw new Error(`Ошибка HTTP: ${response.status}`);
        }

        const campaigns = await response.json();
        if (campaigns.length === 0) {
            showError('Кампания не найдена');
            return;
        }

        campaignData = campaigns[0];
        renderCampaignInfo();
        renderNmList();

        // Автоматически загружаем фразы для всех товаров
        expandAllPhrases();
    } catch (error) {
        showError(`Ошибка загрузки кампании: ${error.message}`);
    } finally {
        showLoading(false);
    }
}

// Отображение информации о кампании
function renderCampaignInfo() {
    const container = document.getElementById('campaignInfo');
    const statusInfo = getStatusInfo(campaignData.status);

    container.innerHTML = `
        <div class="campaign-detail-header">
            <h3>${escapeHtml(campaignData.settings.name)}</h3>
            <span class="campaign-status ${statusInfo.class}">${statusInfo.text}</span>
        </div>
        <div class="campaign-detail-info">
            <div class="info-row">
                <span class="info-label">ID кампании:</span>
                <span class="info-value">${campaignData.id}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Тип ставок:</span>
                <span class="info-value">${campaignData.bid_type === 'manual' ? 'Ручная' : 'Единая'}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Тип оплаты:</span>
                <span class="info-value">${campaignData.settings.payment_type === 'cpm' ? 'CPM' : 'CPC'}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Товаров:</span>
                <span class="info-value">${campaignData.nm_settings.length}</span>
            </div>
        </div>
    `;
}

// Отображение списка товаров в виде таблицы
function renderNmList() {
    const tbody = document.getElementById('nmTableBody');
    if (!tbody) return;

    if (campaignData.nm_settings.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #666; padding: 40px;">В кампании нет товаров</td></tr>';
        return;
    }

    let html = '';
    campaignData.nm_settings.forEach(nm => {
        const phrasesCount = nmPhrasesMap[nm.nm_id] ? nmPhrasesMap[nm.nm_id].length : 0;
        const hasPhrases = phrasesCount > 0;
        const isLoading = nmLoading[nm.nm_id] || false;

        // Основная строка
        html += `
            <tr class="nm-table-row">
                <td class="nm-id-cell">#${nm.nm_id}</td>
                <td class="nm-subject-cell">${nm.subject ? nm.subject.name : 'Не указано'}</td>
                <td class="nm-bid-cell">${nm.bids_kopecks ? nm.bids_kopecks.search / 100 : 0} ₽</td>
                <td class="nm-phrases-count-cell ${hasPhrases ? 'has' : 'zero'}">
                    ${hasPhrases ? phrasesCount : '—'}
                </td>
                <td class="nm-actions-cell">
                    <span style="color: #999; font-size: 13px;">${hasPhrases ? `${phrasesCount} фраз` : 'Нет фраз'}</span>
                </td>
            </tr>
        `;

        // Всегда показываем секцию с фразами
        html += `
            <tr class="nm-expanded-row">
                <td colspan="5">
                    <div class="nm-expanded-content">
                        ${isLoading ? `
                            <div class="load-status">
                                <span class="spinner-small"></span> Загрузка минус-фраз...
                            </div>
                        ` : `
                            <div class="nm-phrases-wrapper">
                                <textarea class="nm-phrases-textarea" id="phrasesTextarea-${nm.nm_id}" placeholder="Введите минус-фразы, каждую с новой строки">${(nmPhrasesMap[nm.nm_id] || []).join('\n')}</textarea>
                                <div class="nm-phrases-list" id="phrasesList-${nm.nm_id}">
                                    ${(nmPhrasesMap[nm.nm_id] || []).length > 0 ? (nmPhrasesMap[nm.nm_id] || []).map((phrase, idx) => `
                                        <div class="phrase-tag">
                                            <span class="phrase-text">${escapeHtml(phrase)}</span>
                                            <button class="remove-phrase-btn" data-nm="${nm.nm_id}" data-index="${idx}" title="Удалить фразу">×</button>
                                        </div>
                                    `).join('') : '<p class="no-phrases">Минус-фраз нет</p>'}
                                </div>
                                <div class="nm-phrases-actions">
                                    <button class="btn btn-primary" onclick="savePhrasesForNm(${nm.nm_id})">💾 Сохранить</button>
                                </div>
                            </div>
                        `}
                    </div>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;

    // Добавляем обработчики для кнопок удаления
    document.querySelectorAll('.remove-phrase-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const nmId = parseInt(this.getAttribute('data-nm'));
            const index = parseInt(this.getAttribute('data-index'));
            removePhraseFromNm(nmId, index);
        });
    });
}

// Состояние загрузки для каждого товара
let nmLoading = {};

// Загрузка фраз для конкретного товара
async function loadPhrasesForNm(nmId) {
    // Если уже загружено или загружается - не загружаем повторно
    if (nmPhrasesMap[nmId] || nmLoading[nmId]) return;
    
    nmLoading[nmId] = true;
    renderNmList();

    try {
        const response = await fetch('/search-clusters/minus-phrases', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify([{ advert_id: currentCampaignId, nm_id: nmId }])
        });

        if (!response.ok) throw new Error(`Ошибка: ${response.status}`);

        const data = await response.json();
        currentPhrases = [];

        const items = data.items || data.data || (Array.isArray(data) ? data : []);
        if (Array.isArray(items)) {
            for (const item of items) {
                let phrases = item.norm_queries || item.excluded || item.minus_phrases || item.phrases || [];
                if (Array.isArray(phrases)) {
                    currentPhrases = phrases;
                    break;
                }
            }
        }

        nmPhrasesMap[nmId] = currentPhrases;
    } catch (error) {
        console.error('Ошибка загрузки:', error);
        nmPhrasesMap[nmId] = [];
    } finally {
        nmLoading[nmId] = false;
        renderNmList();
    }
}

// Сохранение фраз для конкретного товара
async function savePhrasesForNm(nmId) {
    const textarea = document.getElementById(`phrasesTextarea-${nmId}`);
    const newPhrases = textarea.value.trim().split('\n').filter(p => p.trim());

    if (newPhrases.length === 0 && (nmPhrasesMap[nmId] || []).length === 0) {
        togglePhrasesSection(nmId);
        return;
    }

    try {
        const response = await fetch('/search-clusters/set-minus-phrases', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                advert_id: currentCampaignId,
                nm_id: nmId,
                norm_queries: newPhrases
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `Ошибка: ${response.status}`);
        }

        nmPhrasesMap[nmId] = newPhrases;
        renderNmList();
        alert('Минус-фразы сохранены!');
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

// Удаление фразы
async function removePhraseFromNm(nmId, index) {
    const phrase = (nmPhrasesMap[nmId] || [])[index];
    if (!phrase || !confirm(`Удалить "${phrase}"?`)) return;

    try {
        const updated = (nmPhrasesMap[nmId] || []).filter((_, i) => i !== index);
        const response = await fetch('/search-clusters/set-minus-phrases', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                advert_id: currentCampaignId,
                nm_id: nmId,
                norm_queries: updated
            })
        });

        if (!response.ok) throw new Error(`Ошибка: ${response.status}`);

        nmPhrasesMap[nmId] = updated;
        renderNmList();
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
}

// Автоматическая загрузка фраз для всех товаров при загрузке страницы
async function expandAllPhrases() {
    for (const nm of campaignData.nm_settings) {
        await loadPhrasesForNm(nm.nm_id);
    }
}

// Вспомогательные функции
function getStatusInfo(status) {
    const statusMap = {
        '-1': { text: 'Удалена', class: 'status-stopped' },
        '4': { text: 'Готова к запуску', class: 'status-draft' },
        '7': { text: 'Завершена', class: 'status-completed' },
        '8': { text: 'Отменена', class: 'status-stopped' },
        '9': { text: 'Активна', class: 'status-active' },
        '11': { text: 'На паузе', class: 'status-paused' }
    };
    return statusMap[status] || { text: status, class: '' };
}

function showLoading(show) {
    const indicator = document.getElementById('loadingIndicator');
    if (show) {
        indicator.classList.remove('hidden');
    } else {
        indicator.classList.add('hidden');
    }
}

function showError(message) {
    const container = document.getElementById('errorContainer');
    container.textContent = message;
    container.classList.remove('hidden');
}

function hideError() {
    document.getElementById('errorContainer').classList.add('hidden');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ==================== Функции кластеров ====================

// Открытие модального окна кластеров
function openClustersModal() {
    document.getElementById('clustersModal').classList.remove('hidden');
    populateNmSelect();
}

// Закрытие модального окна кластеров
function closeClustersModal() {
    document.getElementById('clustersModal').classList.add('hidden');
    clustersData = { active: [], excluded: [] };
    selectedClusters = [];
}

// Заполнение селекта товарами
function populateNmSelect() {
    const select = document.getElementById('clusterNmSelect');
    select.innerHTML = '<option value="">Выберите товар</option>';
    
    if (!campaignData || !campaignData.nm_settings) return;
    
    campaignData.nm_settings.forEach(nm => {
        const option = document.createElement('option');
        option.value = nm.nm_id;
        option.textContent = `Товар #${nm.nm_id} - ${nm.subject ? nm.subject.name : 'Не указано'}`;
        select.appendChild(option);
    });
}

// Загрузка кластеров
async function loadClusters() {
    const nmId = document.getElementById('clusterNmSelect').value;
    if (!nmId) {
        document.getElementById('clustersContent').classList.add('hidden');
        return;
    }
    
    const loading = document.getElementById('clustersLoading');
    const content = document.getElementById('clustersContent');
    const error = document.getElementById('clustersError');
    
    loading.classList.remove('hidden');
    content.classList.add('hidden');
    error.classList.add('hidden');
    
    try {
        const response = await fetch('/search-clusters/list', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify([{
                advert_id: currentCampaignId,
                nm_id: parseInt(nmId)
            }])
        });
        
        if (!response.ok) {
            throw new Error(`Ошибка: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Clusters response:', data);
        
        // Парсим ответ API
        // Структура: {items: [{advertId, nmId, normQueries: {active: [], excluded: []}}]}
        clustersData = { active: [], excluded: [] };
        const items = data.items || [];
        
        for (const item of items) {
            if (item.advertId === currentCampaignId && item.nmId === parseInt(nmId)) {
                // Проверяем разные форматы ответа
                if (item.normQueries) {
                    clustersData.active = item.normQueries.active || [];
                    clustersData.excluded = item.normQueries.excluded || [];
                } else if (item.active) {
                    clustersData.active = item.active || [];
                    clustersData.excluded = item.excluded || [];
                }
                break;
            }
        }
        
        updateClustersSummary();
        renderClusters();
        
        loading.classList.add('hidden');
        content.classList.remove('hidden');
        
    } catch (error) {
        console.error('Ошибка загрузки кластеров:', error);
        error.textContent = 'Ошибка загрузки: ' + error.message;
        error.classList.remove('hidden');
        loading.classList.add('hidden');
    }
}

// Обновление сводки
function updateClustersSummary() {
    document.getElementById('activeCount').textContent = clustersData.active.length;
    document.getElementById('excludedCount').textContent = clustersData.excluded.length;
}

// Отображение кластеров
function renderClusters() {
    const container = document.getElementById('clustersList');
    const filter = document.getElementById('clusterTypeFilter').value;
    
    let items = [];
    
    if (filter === 'all' || filter === 'active') {
        items = items.concat(clustersData.active.map(q => ({ query: q, type: 'active' })));
    }
    
    if (filter === 'all' || filter === 'excluded') {
        items = items.concat(clustersData.excluded.map(q => ({ query: q, type: 'excluded' })));
    }
    
    if (items.length === 0) {
        container.innerHTML = '<p class="no-phrases">Кластеров не найдено</p>';
        return;
    }
    
    container.innerHTML = items.map(item => {
        const isSelected = selectedClusters.includes(item.query);
        return `
            <div class="cluster-item ${isSelected ? 'selected' : ''}" data-query="${escapeHtml(item.query)}">
                <input type="checkbox" class="cluster-checkbox" 
                    ${isSelected ? 'checked' : ''} 
                    onchange="toggleClusterSelection('${escapeHtml(item.query)}')">
                <span class="cluster-text">${escapeHtml(item.query)}</span>
                <span class="cluster-type ${item.type}">${item.type === 'active' ? 'Активный' : 'Исключён'}</span>
            </div>
        `;
    }).join('');
}

// Переключение выбора кластера
function toggleClusterSelection(query) {
    const index = selectedClusters.indexOf(query);
    if (index > -1) {
        selectedClusters.splice(index, 1);
    } else {
        selectedClusters.push(query);
    }
    
    // Обновляем визуальное выделение
    const item = document.querySelector(`.cluster-item[data-query="${CSS.escape(query)}"]`);
    if (item) {
        item.classList.toggle('selected', selectedClusters.includes(query));
    }
}

// Выбрать все
function toggleSelectAll() {
    const filter = document.getElementById('clusterTypeFilter').value;
    
    if (selectedClusters.length > 0 && 
        ((filter === 'active' && selectedClusters.length === clustersData.active.length) ||
         (filter === 'excluded' && selectedClusters.length === clustersData.excluded.length))) {
        // Снять все
        selectedClusters = [];
    } else {
        // Выбрать все видимые
        selectedClusters = [];
        if (filter === 'all' || filter === 'active') {
            selectedClusters = [...clustersData.active];
        }
        if (filter === 'all' || filter === 'excluded') {
            selectedClusters = [...new Set([...selectedClusters, ...clustersData.excluded])];
        }
    }
    
    renderClusters();
}

// Добавить выбранные в минус-фразы
async function addSelectedToMinus() {
    const nmId = document.getElementById('clusterNmSelect').value;
    if (!nmId) {
        alert('Выберите товар');
        return;
    }
    
    if (selectedClusters.length === 0) {
        alert('Выберите кластеры для добавления');
        return;
    }
    
    if (!confirm(`Добавить ${selectedClusters.length} кластер(ов) в минус-фразы для товара #${nmId}?`)) {
        return;
    }
    
    try {
        // Загружаем текущие минус-фразы
        const currentResponse = await fetch('/search-clusters/minus-phrases', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify([{
                advert_id: currentCampaignId,
                nm_id: parseInt(nmId)
            }])
        });
        
        let currentPhrases = [];
        if (currentResponse.ok) {
            const data = await currentResponse.json();
            const items = data.items || data.stats || [];
            for (const item of items) {
                if (item.advert_id === currentCampaignId && item.nm_id === parseInt(nmId)) {
                    const phraseList = item.stats || item.norm_queries || item.excluded || [];
                    if (Array.isArray(phraseList)) {
                        currentPhrases = phraseList.map(p => p.norm_query || p).filter(p => p);
                    }
                    break;
                }
            }
        }
        
        // Добавляем новые кластеры к существующим
        const allPhrases = [...new Set([...currentPhrases, ...selectedClusters])];
        
        const response = await fetch('/search-clusters/set-minus-phrases', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                advert_id: currentCampaignId,
                nm_id: parseInt(nmId),
                norm_queries: allPhrases
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Ошибка при сохранении');
        }
        
        alert(`Добавлено ${selectedClusters.length} кластер(ов) в минус-фразы для товара #${nmId}\nВсего фраз: ${allPhrases.length}`);
        
        // Обновляем данные
        selectedClusters = [];
        await loadClusters();
        
        // Обновляем мапу и список товаров
        if (!nmPhrasesMap[parseInt(nmId)]) {
            nmPhrasesMap[parseInt(nmId)] = [];
        }
        renderNmList();
        
        // Если открыто модальное окно минус-фраз для этого товара
        if (currentNmId === parseInt(nmId)) {
            await loadMinusPhrases(currentCampaignId, currentNmId);
        }
        
    } catch (error) {
        console.error('Ошибка добавления кластеров:', error);
        alert('Ошибка: ' + error.message);
    }
}

// ==================== Функции статистики ====================

// Открытие модального окна статистики
function openStatsModal() {
    document.getElementById('statsModal').classList.remove('hidden');
    initStatsDates();
}

// Закрытие модального окна статистики
function closeStatsModal() {
    document.getElementById('statsModal').classList.add('hidden');
    document.getElementById('statsContent').classList.add('hidden');
}

// ==================== Полная статистика ====================

// Открытие модального окна полной статистики
function openFullStatsModal() {
    document.getElementById('fullStatsModal').classList.remove('hidden');
    initFullStatsDates();
}

// Закрытие модального окна полной статистики
function closeFullStatsModal() {
    document.getElementById('fullStatsModal').classList.add('hidden');
    document.getElementById('fullStatsContent').classList.add('hidden');
}

// Инициализация дат (последние 7 дней)
function initFullStatsDates() {
    const today = new Date();
    const weekAgo = new Date(today);
    weekAgo.setDate(weekAgo.getDate() - 7);

    document.getElementById('fullStatsFromDate').value = weekAgo.toISOString().split('T')[0];
    document.getElementById('fullStatsToDate').value = today.toISOString().split('T')[0];
}

// Загрузка полной статистики
async function loadFullStats() {
    const fromDate = document.getElementById('fullStatsFromDate').value;
    const toDate = document.getElementById('fullStatsToDate').value;

    if (!fromDate || !toDate) {
        alert('Выберите даты периода');
        return;
    }

    const loading = document.getElementById('fullStatsLoading');
    const content = document.getElementById('fullStatsContent');
    const error = document.getElementById('fullStatsError');

    loading.classList.remove('hidden');
    content.classList.add('hidden');
    error.classList.add('hidden');

    try {
        const ids = campaignData.nm_settings.map(nm => nm.nm_id);

        const response = await fetch('/stats/full', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                ids: [currentCampaignId],
                from_date: fromDate,
                to_date: toDate
            })
        });

        if (!response.ok) {
            throw new Error(`Ошибка: ${response.status}`);
        }

        const data = await response.json();
        console.log('Full stats response:', data);

        renderFullStats(data);

        loading.classList.add('hidden');
        content.classList.remove('hidden');

    } catch (error) {
        console.error('Ошибка загрузки полной статистики:', error);
        error.textContent = 'Ошибка: ' + error.message;
        error.classList.remove('hidden');
        loading.classList.add('hidden');
    }
}

// Отображение полной статистики с детализацией по дням
function renderFullStats(data) {
    const campaigns = data.campaigns || [];

    let totalViews = 0;
    let totalClicks = 0;
    let totalOrders = 0;
    let totalRevenue = 0;
    let totalSpend = 0;
    let totalCpc = 0;

    const campaignsHtml = campaigns.map(camp => {
        const campViews = camp.total_views || 0;
        const campClicks = camp.total_clicks || 0;
        const campOrders = camp.total_orders || 0;
        const campRevenue = camp.total_revenue || 0;
        const campSpend = camp.total_sum_price || 0;
        const campCpc = camp.avg_cpc || 0;

        totalViews += campViews;
        totalClicks += campClicks;
        totalOrders += campOrders;
        totalRevenue += campRevenue;
        totalSpend += campSpend;
        totalCpc += campCpc;

        // Сводка по кампании
        const campCtr = campViews > 0 ? (campClicks / campViews * 100) : 0;
        const campCr = campClicks > 0 ? (campOrders / campClicks * 100) : 0;

        // Детализация по дням
        const daysHtml = (camp.days || []).map(day => {
            const dayDate = new Date(day.date).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' });
            const dayCtr = day.views > 0 ? (day.clicks / day.views * 100) : 0;
            const dayCr = day.clicks > 0 ? (day.orders / day.clicks * 100) : 0;

            // Детализация по приложениям внутри дня
            const appsHtml = (day.apps || []).map(app => {
                const appTypeName = getAppTypeName(app.app_type);
                const appCtr = app.views > 0 ? (app.clicks / app.views * 100) : 0;
                const appCr = app.clicks > 0 ? (app.orders / app.clicks * 100) : 0;

                // Детализация по товарам внутри приложения
                const nmsHtml = (app.nms || []).map(nm => {
                    const nmCtr = nm.views > 0 ? (nm.clicks / nm.views * 100) : 0;
                    const nmCr = nm.clicks > 0 ? (nm.orders / nm.clicks * 100) : 0;

                    return `
                        <div class="stat-row stat-nm">
                            <td class="nm-name" title="${escapeHtml(nm.name)}">${escapeHtml(nm.name)}</td>
                            <td>${nm.views.toLocaleString()}</td>
                            <td>${nm.clicks.toLocaleString()}</td>
                            <td>${nmCtr.toFixed(2)}%</td>
                            <td>${nm.orders.toLocaleString()}</td>
                            <td>${nmCr.toFixed(2)}%</td>
                            <td>${nm.sum.toFixed(2)} ₽</td>
                            <td>${nm.cpc.toFixed(2)} ₽</td>
                            <td>${nm.atbs.toLocaleString()}</td>
                            <td>${nm.canceled.toLocaleString()}</td>
                        </div>
                    `;
                }).join('');

                return `
                    <div class="stat-block app-block">
                        <div class="stat-header">
                            <strong>📱 ${appTypeName}</strong>
                            <span class="stat-metrics">
                                Просмотры: ${app.views.toLocaleString()} | 
                                Клики: ${app.clicks.toLocaleString()} | 
                                CTR: ${appCtr.toFixed(2)}% | 
                                Заказы: ${app.orders.toLocaleString()} | 
                                CR: ${appCr.toFixed(2)}% | 
                                Выручка: ${app.sum.toFixed(2)} ₽ | 
                                CPC: ${app.cpc.toFixed(2)} ₽
                            </span>
                        </div>
                        ${app.nms && app.nms.length > 0 ? `
                            <table class="stats-detail-table">
                                <thead>
                                    <tr>
                                        <th>Товар</th>
                                        <th>Просмотры</th>
                                        <th>Клики</th>
                                        <th>CTR</th>
                                        <th>Заказы</th>
                                        <th>CR</th>
                                        <th>Выручка</th>
                                        <th>CPC</th>
                                        <th>ATBs</th>
                                        <th>Отмены</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${nmsHtml}
                                </tbody>
                            </table>
                        ` : '<p class="no-data">Нет данных по товарам</p>'}
                    </div>
                `;
            }).join('');

            return `
                <div class="stat-block day-block">
                    <div class="stat-header day-header">
                        <strong>📅 ${dayDate}</strong>
                        <span class="stat-metrics">
                            Просмотры: ${day.views.toLocaleString()} | 
                            Клики: ${day.clicks.toLocaleString()} | 
                            CTR: ${dayCtr.toFixed(2)}% | 
                            Заказы: ${day.orders.toLocaleString()} | 
                            CR: ${dayCr.toFixed(2)}% | 
                            Выручка: ${day.sum.toFixed(2)} ₽ | 
                            Затраты: ${day.sum_price.toFixed(2)} ₽
                        </span>
                    </div>
                    ${day.apps && day.apps.length > 0 ? appsHtml : '<p class="no-data">Нет данных по приложениям</p>'}
                </div>
            `;
        }).join('');

        // Агрегированные товары
        const itemsHtml = (camp.items || []).map(item => {
            return `
                <div class="full-stat-nm">
                    <div class="nm-header">
                        <span class="nm-id">Товар #${item.nm_id}</span>
                        <span class="nm-name">${escapeHtml(item.subject)}</span>
                    </div>
                    <div class="nm-stats-grid">
                        <div class="nm-stat"><span class="nm-label">Просмотры:</span> <span class="nm-value">${item.total_views.toLocaleString()}</span></div>
                        <div class="nm-stat"><span class="nm-label">Клики:</span> <span class="nm-value">${item.total_clicks.toLocaleString()}</span></div>
                        <div class="nm-stat"><span class="nm-label">CTR:</span> <span class="nm-value">${item.total_ctr.toFixed(2)}%</span></div>
                        <div class="nm-stat"><span class="nm-label">Заказы:</span> <span class="nm-value">${item.total_orders.toLocaleString()}</span></div>
                        <div class="nm-stat"><span class="nm-label">CR:</span> <span class="nm-value">${item.total_cr.toFixed(2)}%</span></div>
                        <div class="nm-stat"><span class="nm-label">Выручка:</span> <span class="nm-value">${item.total_revenue.toFixed(2)} ₽</span></div>
                        <div class="nm-stat"><span class="nm-label">CPC:</span> <span class="nm-value">${item.total_cpc.toFixed(2)} ₽</span></div>
                    </div>
                </div>
            `;
        }).join('');

        return `
            <div class="full-stat-campaign">
                <h3>📊 ${escapeHtml(camp.name || 'Кампания #' + camp.id)}</h3>
                <div class="campaign-summary-card">
                    <div class="summary-grid">
                        <div class="summary-item">
                            <div class="summary-label">Просмотры</div>
                            <div class="summary-value">${campViews.toLocaleString()}</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-label">Клики</div>
                            <div class="summary-value">${campClicks.toLocaleString()}</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-label">CTR</div>
                            <div class="summary-value">${campCtr.toFixed(2)}%</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-label">Заказы</div>
                            <div class="summary-value">${campOrders.toLocaleString()}</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-label">CR</div>
                            <div class="summary-value">${campCr.toFixed(2)}%</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-label">Выручка</div>
                            <div class="summary-value">${campRevenue.toFixed(2)} ₽</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-label">Затраты</div>
                            <div class="summary-value">${campSpend.toFixed(2)} ₽</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-label">CPC</div>
                            <div class="summary-value">${campCpc.toFixed(2)} ₽</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-label">ATBs</div>
                            <div class="summary-value">${camp.total_atbs.toLocaleString()}</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-label">Отмены</div>
                            <div class="summary-value">${camp.total_canceled.toLocaleString()}</div>
                        </div>
                    </div>
                </div>

                <details class="detail-section" open>
                    <summary>📅 Статистика по дням</summary>
                    <div class="days-container">
                        ${daysHtml}
                    </div>
                </details>

                <details class="detail-section">
                    <summary>📦 Товары (агрегировано)</summary>
                    <div class="items-container">
                        ${itemsHtml}
                    </div>
                </details>
            </div>
        `;
    }).join('');

    const avgCpc = campaigns.length > 0 ? (totalCpc / campaigns.length) : 0;
    const totalCtr = totalViews > 0 ? (totalClicks / totalViews * 100) : 0;
    const totalCr = totalClicks > 0 ? (totalOrders / totalClicks * 100) : 0;

    document.getElementById('fullTotalViews').textContent = totalViews.toLocaleString();
    document.getElementById('fullTotalClicks').textContent = totalClicks.toLocaleString();
    document.getElementById('fullTotalOrders').textContent = totalOrders.toLocaleString();
    document.getElementById('fullTotalRevenue').textContent = totalRevenue.toFixed(2) + ' ₽';
    document.getElementById('fullTotalSpend').textContent = totalSpend.toFixed(2) + ' ₽';
    document.getElementById('fullTotalCtr').textContent = totalCtr.toFixed(2) + '%';

    document.getElementById('fullStatsCampaigns').innerHTML = campaignsHtml || '<p class="no-phrases">Нет данных</p>';
}

// Получение названия типа приложения
function getAppTypeName(appType) {
    const typeMap = {
        1: 'Веб-сайт',
        32: 'iOS',
        64: 'Android',
        128: 'WAP'
    };
    return typeMap[appType] || `Тип ${appType}`;
}

// Загрузка статистики
async function loadStats() {
    const fromDate = document.getElementById('statsFromDate').value;
    const toDate = document.getElementById('statsToDate').value;
    
    if (!fromDate || !toDate) {
        alert('Выберите даты периода');
        return;
    }
    
    const loading = document.getElementById('statsLoading');
    const content = document.getElementById('statsContent');
    const error = document.getElementById('statsError');
    
    loading.classList.remove('hidden');
    content.classList.add('hidden');
    error.classList.add('hidden');
    
    try {
        // Собираем все nm_id из кампании
        const items = campaignData.nm_settings.map(nm => ({
            advert_id: currentCampaignId,
            nm_id: nm.nm_id
        }));
        
        const response = await fetch('/stats/normquery', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                from_date: fromDate,
                to_date: toDate,
                items: items
            })
        });
        
        if (!response.ok) {
            throw new Error(`Ошибка: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Stats response:', data);
        
        // Собираем все фразы из всех товаров
        statsPhrases = [];
        if (data.items && Array.isArray(data.items)) {
            for (const item of data.items) {
                if (item.phrases && Array.isArray(item.phrases)) {
                    for (const phrase of item.phrases) {
                        statsPhrases.push({
                            ...phrase,
                            nm_id: item.nm_id
                        });
                    }
                }
            }
        }
        
        renderStatsTable();
        updateStatsSummary();
        
        loading.classList.add('hidden');
        content.classList.remove('hidden');
        
    } catch (error) {
        console.error('Ошибка загрузки статистики:', error);
        error.textContent = 'Ошибка загрузки статистики: ' + error.message;
        error.classList.remove('hidden');
        loading.classList.add('hidden');
    }
}

// Отображение таблицы статистики
function renderStatsTable() {
    const tbody = document.getElementById('statsTableBody');
    const sortBy = document.getElementById('statsSort').value;
    const filterBy = document.getElementById('statsFilter').value;
    
    if (statsPhrases.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; color: #666;">Нет данных</td></tr>';
        return;
    }
    
    // Собираем все минус-фразы по всем товарам
    const allMinusPhrases = new Set();
    Object.values(nmPhrasesMap).forEach(phrases => {
        phrases.forEach(p => allMinusPhrases.add(p));
    });
    
    // Применяем фильтр
    let filtered = filterStatsPhrases(statsPhrases, filterBy);

    // Сортируем
    let sorted = sortStatsPhrases(filtered, sortBy);

    if (sorted.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; color: #666;">По фильтру ничего не найдено</td></tr>';
        return;
    }

    // Расчитываем средний CPC для сравнения
    const avgCpc = calculateAvgCpc();

    tbody.innerHTML = sorted.map(phrase => {
        const efficiency = calculateEfficiency(phrase, avgCpc);
        const efficiencyClass = getEfficiencyClass(efficiency);
        const isInMinus = allMinusPhrases.has(phrase.norm_query);
        const cpcInfo = getCpcExpensiveness(phrase, avgCpc);

        return `
            <tr class="phrase-row ${efficiencyClass} ${isInMinus ? 'in-minus' : ''}">
                <td class="phrase-cell" title="${escapeHtml(phrase.norm_query)}">
                    ${isInMinus ? '<span class="minus-indicator" title="Уже в минус-фразах">🚫</span>' : ''}
                    ${escapeHtml(phrase.norm_query)}
                </td>
                <td>${phrase.views.toLocaleString()}</td>
                <td>${phrase.clicks.toLocaleString()}</td>
                <td>${phrase.ctr.toFixed(2)}%</td>
                <td>${phrase.orders.toLocaleString()}</td>
                <td>${phrase.spend.toFixed(2)} ₽</td>
                <td>
                    <span class="cpc-value ${cpcInfo.class}" title="${cpcInfo.percent > 0 ? 'Дороже' : 'Дешевле'} среднего на ${Math.abs(cpcInfo.percent).toFixed(0)}%">
                        ${phrase.cpc.toFixed(2)} ₽
                        ${cpcInfo.percent !== 0 ? `<span class="cpc-delta">${cpcInfo.percent > 0 ? '+' : ''}${cpcInfo.percent.toFixed(0)}%</span>` : ''}
                    </span>
                </td>
                <td><span class="efficiency-badge ${efficiencyClass}">${efficiency}</span></td>
                <td>
                    ${isInMinus
                        ? '<span class="already-in-minus">✓ В минус-фразах</span>'
                        : `<button class="btn btn-sm btn-add-minus" onclick="addPhraseToMinus('${escapeHtml(phrase.norm_query)}')" title="Добавить в минус-фразы">
                            🚫 В минус-фразы
                        </button>`
                    }
                </td>
            </tr>
        `;
    }).join('');
}

// Фильтрация фраз
function filterStatsPhrases(phrases, filter) {
    switch(filter) {
        case 'good':
            // Эффективные: CTR > 5% или есть заказы
            return phrases.filter(p => p.ctr > 5 || p.orders > 0);
        case 'bad':
            // Неэффективные: CTR < 1% и нет заказов и были затраты
            return phrases.filter(p => p.ctr < 1 && p.orders === 0 && p.spend > 0);
        case 'no-clicks':
            // Без кликов: были просмотры но нет кликов
            return phrases.filter(p => p.views > 0 && p.clicks === 0);
        case 'expensive':
            // Дорогие клики: CPC > 50 руб
            return phrases.filter(p => p.cpc > 50);
        default:
            return phrases;
    }
}

// Сортировка фраз
function sortStatsPhrases(phrases, sortBy) {
    const sorted = [...phrases];
    
    switch(sortBy) {
        case 'views':
            return sorted.sort((a, b) => b.views - a.views);
        case 'clicks':
            return sorted.sort((a, b) => b.clicks - a.clicks);
        case 'spend':
            return sorted.sort((a, b) => b.spend - a.spend);
        case 'ctr':
            return sorted.sort((a, b) => b.ctr - a.ctr);
        case 'efficiency':
            return sorted.sort((a, b) => {
                const effA = calculateEfficiencyScore(a);
                const effB = calculateEfficiencyScore(b);
                return effB - effA;
            });
        default:
            return sorted;
    }
}

// Расчёт метрики эффективности (возвращает строку)
function calculateEfficiency(phrase, avgCpc = null) {
    // Отлично: CTR > 10% или есть заказы
    if (phrase.ctr > 10 || phrase.orders > 0) {
        return 'Отлично';
    }
    
    // Хорошо: CTR 5-10%
    if (phrase.ctr >= 5 && phrase.ctr <= 10) {
        return 'Хорошо';
    }
    
    // Нормально: CTR 2-5%
    if (phrase.ctr >= 2 && phrase.ctr < 5) {
        return 'Нормально';
    }
    
    // Плохо: CTR < 2% и нет заказов
    if (phrase.ctr < 2 && phrase.orders === 0) {
        return 'Плохо';
    }
    
    // Ужасно: Просмотры без кликов
    if (phrase.views > 0 && phrase.clicks === 0) {
        return 'Ужасно';
    }
    
    // По умолчанию (нет просмотров)
    return 'Нет данных';
}

// Расчёт числового показателя эффективности (0-100) для сортировки
function calculateEfficiencyScore(phrase, avgCpc = null) {
    // Есть заказы -最高 приоритет
    if (phrase.orders > 0) return 100;
    
    // Высокий CTR
    if (phrase.ctr > 10) return 90;
    if (phrase.ctr >= 5) return 70;
    if (phrase.ctr >= 3) return 50;
    if (phrase.ctr >= 2) return 30;
    
    // Низкий CTR
    if (phrase.ctr > 0) return 10;
    
    // Нет кликов
    if (phrase.views > 0 && phrase.clicks === 0) return 0;
    
    return 0;
}

// Расчёт среднего CPC по всем фразам
function calculateAvgCpc() {
    if (statsPhrases.length === 0) return 0;
    const totalCpc = statsPhrases.reduce((sum, p) => sum + p.cpc, 0);
    return totalCpc / statsPhrases.length;
}

// Насколько дорог клик (возвращает процент и класс)
function getCpcExpensiveness(phrase, avgCpc) {
    if (avgCpc <= 0 || phrase.cpc <= 0) return { percent: 0, class: '' };
    
    const percent = ((phrase.cpc - avgCpc) / avgCpc) * 100;
    
    if (percent > 50) return { percent, class: 'cpc-very-expensive' };
    if (percent > 20) return { percent, class: 'cpc-expensive' };
    if (percent < -20) return { percent, class: 'cpc-cheap' };
    if (percent < -50) return { percent, class: 'cpc-very-cheap' };
    
    return { percent, class: 'cpc-normal' };
}

// Получение CSS класса для эффективности
function getEfficiencyClass(efficiency) {
    switch(efficiency) {
        case 'Отлично': return 'eff-excellent';
        case 'Хорошо': return 'eff-good';
        case 'Нормально': return 'eff-average';
        case 'Плохо': return 'eff-bad';
        case 'Ужасно': return 'eff-terrible';
        default: return '';
    }
}

// Обновление сводки статистики
function updateStatsSummary() {
    const totalViews = statsPhrases.reduce((sum, p) => sum + p.views, 0);
    const totalClicks = statsPhrases.reduce((sum, p) => sum + p.clicks, 0);
    const totalOrders = statsPhrases.reduce((sum, p) => sum + p.orders, 0);
    const totalSpend = statsPhrases.reduce((sum, p) => sum + p.spend, 0);
    const ctr = totalViews > 0 ? (totalClicks / totalViews * 100) : 0;
    
    document.getElementById('totalViews').textContent = totalViews.toLocaleString();
    document.getElementById('totalClicks').textContent = totalClicks.toLocaleString();
    document.getElementById('totalOrders').textContent = totalOrders.toLocaleString();
    document.getElementById('totalSpend').textContent = totalSpend.toFixed(2) + ' ₽';
    document.getElementById('totalCtr').textContent = ctr.toFixed(2) + '%';
}

// Добавление фразы в минус-фразы
function addPhraseToMinus(phrase) {
    // Открываем модальное окно выбора товара
    currentPhraseToAdd = phrase;
    document.getElementById('phraseToAdd').textContent = phrase;
    renderProductList();
    document.getElementById('productSelectModal').classList.remove('hidden');
}

// Закрытие модального окна выбора товара
function closeProductSelectModal() {
    document.getElementById('productSelectModal').classList.add('hidden');
    currentPhraseToAdd = null;
}

// Отображение списка товаров для выбора
function renderProductList() {
    const container = document.getElementById('productList');
    
    if (!campaignData || !campaignData.nm_settings) {
        container.innerHTML = '<p class="error-message">Нет данных о товарах</p>';
        return;
    }
    
    container.innerHTML = campaignData.nm_settings.map(nm => `
        <div class="product-item" onclick="selectProductForMinus(${nm.nm_id})">
            <div class="product-nm-id">Товар #${nm.nm_id}</div>
            <div class="product-subject">${nm.subject ? nm.subject.name : 'Не указано'}</div>
            <div class="product-bid">
                Ставка: ${nm.bids_kopecks ? nm.bids_kopecks.search / 100 : 0} ₽
            </div>
        </div>
    `).join('');
}

// Выбор товара для добавления минус-фразы
async function selectProductForMinus(nmId) {
    if (!currentPhraseToAdd) return;
    
    try {
        // Сначала загружаем текущие минус-фразы для этого товара
        const currentResponse = await fetch('/search-clusters/minus-phrases', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify([{
                advert_id: currentCampaignId,
                nm_id: nmId
            }])
        });
        
        let currentPhrases = [];
        if (currentResponse.ok) {
            const data = await currentResponse.json();
            const items = data.items || data.stats || [];
            for (const item of items) {
                if (item.advert_id === currentCampaignId && item.nm_id === nmId) {
                    const phraseList = item.stats || item.norm_queries || item.excluded || [];
                    if (Array.isArray(phraseList)) {
                        currentPhrases = phraseList.map(p => p.norm_query || p).filter(p => p);
                    }
                    break;
                }
            }
        }
        
        // Проверяем, нет ли уже такой фразы
        if (currentPhrases.includes(currentPhraseToAdd)) {
            alert(`Фраза "${currentPhraseToAdd}" уже есть в минус-фразах`);
            closeProductSelectModal();
            return;
        }
        
        // Добавляем новую фразу к существующим
        const allPhrases = [...currentPhrases, currentPhraseToAdd];
        
        const response = await fetch('/search-clusters/set-minus-phrases', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                advert_id: currentCampaignId,
                nm_id: nmId,
                norm_queries: allPhrases
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Ошибка при сохранении');
        }
        
        // Закрываем модальное окно
        closeProductSelectModal();
        
        // Обновляем данные в модальном окне минус-фраз если оно открыто для этого товара
        if (currentNmId === nmId) {
            await loadMinusPhrases(currentCampaignId, currentNmId);
        }
        
        // Обновляем мапу
        if (!nmPhrasesMap[nmId]) {
            nmPhrasesMap[nmId] = [];
        }
        nmPhrasesMap[nmId].push(currentPhraseToAdd);
        renderNmList();
        
        alert(`Фраза "${currentPhraseToAdd}" добавлена в минус-фразы для товара #${nmId}\nВсего фраз: ${allPhrases.length}`);
        
    } catch (error) {
        console.error('Ошибка добавления в минус-фразы:', error);
        alert('Ошибка: ' + error.message);
    }
}
