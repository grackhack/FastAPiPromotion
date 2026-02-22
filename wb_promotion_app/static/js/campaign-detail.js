// campaign-detail.js - Упрощённая версия для управления кампанией

let currentCampaignId = null;
let campaignData = null;
let currentApiToken = null;

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Проверяем есть ли данные кампании в шаблоне (SSR)
    const campaignDataEl = document.getElementById('campaign-data');

    if (campaignDataEl && campaignDataEl.textContent.trim()) {
        try {
            campaignData = JSON.parse(campaignDataEl.textContent);
            currentCampaignId = campaignData.id;
            renderCampaignInfo();
            renderNmList();
            console.log('Кампания загружена через SSR');
        } catch (e) {
            console.error('Ошибка парсинга JSON кампании:', e);
            showError('Ошибка загрузки данных кампании');
        }
    } else {
        // Данных нет - загружаем через API
        currentCampaignId = parseInt(document.getElementById('campaignId').textContent);
        loadCampaignData();
    }

    loadApiToken();
});

// Загрузка API токена из сессии
async function loadApiToken() {
    try {
        const response = await fetch('/auth/token');
        const data = await response.json();
        if (data.has_token && data.token) {
            currentApiToken = data.token;
            console.log('API токен загружен');
        } else {
            console.warn('API токен не найден');
        }
    } catch (error) {
        console.error('Ошибка загрузки токена:', error);
    }
}

// Вспомогательная функция для API запросов
async function apiFetch(url, options = {}) {
    const headers = options.headers || {};
    headers['Content-Type'] = 'application/json';
    
    if (currentApiToken && (url.startsWith('/api/') || url.startsWith('/search-clusters/'))) {
        headers['X-API-Token'] = currentApiToken;
    }

    return fetch(url, {
        ...options,
        headers
    });
}

// Загрузка данных кампании
async function loadCampaignData() {
    showLoading(true);
    
    try {
        const response = await apiFetch(`/api/campaigns?ids=${currentCampaignId}`);
        
        if (!response.ok) {
            throw new Error(`Ошибка HTTP: ${response.status}`);
        }

        const campaigns = await response.json();
        if (!campaigns || campaigns.length === 0) {
            throw new Error('Кампания не найдена');
        }

        campaignData = campaigns[0];
        currentCampaignId = campaignData.id;
        
        renderCampaignInfo();
        renderNmList();
    } catch (error) {
        console.error('Ошибка загрузки кампании:', error);
        showError(`Ошибка: ${error.message}`);
    } finally {
        showLoading(false);
    }
}

// Рендер информации о кампании
function renderCampaignInfo() {
    if (!campaignData) return;

    const container = document.getElementById('campaignInfo');
    if (!container) return;

    const statusClass = getStatusClass(campaignData.status);
    const statusText = getStatusText(campaignData.status);

    container.innerHTML = `
        <div class="campaign-summary">
            <div class="summary-row">
                <span class="summary-label">Название:</span>
                <span class="summary-value">${escapeHtml(campaignData.name || '—')}</span>
            </div>
            <div class="summary-row">
                <span class="summary-label">Статус:</span>
                <span class="summary-value">
                    <span class="status-badge ${statusClass}">${statusText}</span>
                </span>
            </div>
            <div class="summary-row">
                <span class="summary-label">Тип:</span>
                <span class="summary-value">${getTypeText(campaignData.type)}</span>
            </div>
            ${campaignData.daily_budget ? `
            <div class="summary-row">
                <span class="summary-label">Дневной бюджет:</span>
                <span class="summary-value">${campaignData.daily_budget} ₽</span>
            </div>
            ` : ''}
        </div>
    `;
}

// Рендер списка товаров
function renderNmList() {
    if (!campaignData || !campaignData.nm_settings) return;

    const tbody = document.getElementById('nmTableBody');
    if (!tbody) return;

    tbody.innerHTML = '';

    campaignData.nm_settings.forEach(nm => {
        const tr = document.createElement('tr');
        // Ссылка на полную статистику с использованием нового API /adv/v3/fullstats
        tr.innerHTML = `
            <td>${nm.nm_id}</td>
            <td>${nm.name || 'Товар ' + nm.nm_id}</td>
            <td>${nm.bid || '—'} ₽</td>
            <td>
                <a href="/stats/campaign/${currentCampaignId}/nm/${nm.nm_id}" class="btn btn-small btn-secondary" target="_blank" style="margin-right: 5px;">
                    📊 Полная статистика
                </a>
                <button class="btn btn-small btn-secondary" onclick="showPhraseStats(${nm.nm_id})">
                    📈 По фразам
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Показать статистику по фразам
function showPhraseStats(nmId) {
    const modal = document.getElementById('phraseStatsModal');
    modal.style.display = 'flex';
    
    // Сохраняем nm_id для использования при загрузке
    window.currentPhraseStatsNmId = nmId;
    
    // Устанавливаем даты (последние 7 дней)
    const today = new Date();
    const lastWeek = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
    
    document.getElementById('phraseFromDate').value = lastWeek.toISOString().split('T')[0];
    document.getElementById('phraseToDate').value = today.toISOString().split('T')[0];
}

// Закрыть модальное окно статистики
function closePhraseStatsModal() {
    document.getElementById('phraseStatsModal').style.display = 'none';
}

// Загрузить статистику по фразам
async function loadPhraseStats() {
    const campaignId = currentCampaignId;
    const nmId = window.currentPhraseStatsNmId;
    const fromDate = document.getElementById('phraseFromDate').value;
    const toDate = document.getElementById('phraseToDate').value;

    const loading = document.getElementById('phraseStatsLoading');
    const content = document.getElementById('phraseStatsContent');
    
    loading.style.display = 'block';
    content.style.display = 'none';

    try {
        const url = `/api/tasks/phrase-daily-stats?campaign_id=${campaignId}&nm_id=${nmId}&from_date=${fromDate}&to_date=${toDate}`;
        const response = await fetch(url);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка загрузки');
        }

        const data = await response.json();
        const items = data.items || [];

        const tbody = document.getElementById('phraseStatsBody');
        
        if (items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 40px;">Нет данных</td></tr>';
        } else {
            // Агрегируем данные
            let rows = [];
            items.forEach(item => {
                const dailyStats = item.dailyStats || [];
                
                dailyStats.forEach(day => {
                    const stat = day.stat;
                    rows.push({
                        date: day.date,
                        query: stat.normQuery,
                        views: stat.views,
                        clicks: stat.clicks,
                        orders: stat.orders,
                        ctr: stat.ctr,
                        cpc: stat.cpc,
                        spend: stat.spend,
                        avgPos: stat.avgPos
                    });
                });
            });

            // Сортируем по дате и просмотрам
            rows.sort((a, b) => {
                if (b.date !== a.date) return b.date.localeCompare(a.date);
                return b.views - a.views;
            });

            tbody.innerHTML = rows.map(row => `
                <tr>
                    <td>${row.date}</td>
                    <td>${row.query}</td>
                    <td class="number">${row.views.toLocaleString()}</td>
                    <td class="number">${row.clicks.toLocaleString()}</td>
                    <td class="number">${row.orders.toLocaleString()}</td>
                    <td class="number">${row.ctr.toFixed(2)}%</td>
                    <td class="number">${row.cpc.toFixed(2)} ₽</td>
                    <td class="number">${row.spend.toFixed(2)} ₽</td>
                    <td class="number">${row.avgPos.toFixed(2)}</td>
                </tr>
            `).join('');
        }

        content.style.display = 'block';
        
    } catch (error) {
        console.error('Error loading phrase stats:', error);
        alert('Ошибка: ' + error.message);
    } finally {
        loading.style.display = 'none';
    }
}

// Закрытие модального окна по клику вне
window.onclick = function(event) {
    const modal = document.getElementById('phraseStatsModal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
}

// Вспомогательные функции
function getStatusClass(status) {
    const map = {
        9: 'status-active',
        11: 'status-paused',
        4: 'status-draft',
        '-1': 'status-stopped',
        7: 'status-stopped',
        8: 'status-stopped'
    };
    return map[status] || '';
}

function getStatusText(status) {
    const map = {
        9: 'Активна',
        11: 'На паузе',
        4: 'Черновик',
        '-1': 'Удалена',
        7: 'Завершена',
        8: 'Отменена'
    };
    return map[status] || status;
}

function getTypeText(type) {
    const map = {
        1: 'Поисковая',
        2: 'Карточка товара',
        3: 'Категория',
        4: 'Медийная'
    };
    return map[type] || type;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showLoading(show) {
    // Заглушка - можно добавить индикатор загрузки
}

function showError(message) {
    console.error(message);
    alert(message);
}
