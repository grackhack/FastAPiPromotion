// campaigns-list.js - Скрипт для управления страницей кампаний

// Глобальное состояние
let promotionCampaigns = [];
let mediaCampaigns = [];
let currentTab = 'promotion';
let currentStatusFilter = 'active'; // 'all', 'active', 'paused', 'draft', 'stopped'

// Статусы кампаний продвижения
const PROMOTION_STATUS_MAP = {
    '-1': { text: 'Удалена', class: 'status-stopped', group: 'stopped' },
    '4': { text: 'Готова к запуску', class: 'status-draft', group: 'draft' },
    '7': { text: 'Завершена', class: 'status-completed', group: 'stopped' },
    '8': { text: 'Отменена', class: 'status-stopped', group: 'stopped' },
    '9': { text: 'Активна', class: 'status-active', group: 'active' },
    '11': { text: 'На паузе', class: 'status-paused', group: 'paused' }
};

// Группы статусов
const STATUS_GROUPS = {
    'active': [9],           // Активные
    'paused': [11],          // На паузе
    'draft': [4],            // Черновики
    'stopped': [-1, 7, 8]    // Остановлены (удалены, завершены, отменены)
};

// Статусы медиакампаний
const MEDIA_STATUS_MAP = {
    '1': { text: 'Черновик', class: 'status-draft' },
    '2': { text: 'Модерация', class: 'status-paused' },
    '3': { text: 'Отклонена', class: 'status-stopped' },
    '4': { text: 'Готова к запуску', class: 'status-draft' },
    '5': { text: 'Запланирована', class: 'status-paused' },
    '6': { text: 'На показах', class: 'status-active' },
    '7': { text: 'Завершена', class: 'status-completed' },
    '8': { text: 'Отменена', class: 'status-stopped' },
    '9': { text: 'Приостановлена', class: 'status-paused' },
    '10': { text: 'Пауза по лимиту', class: 'status-paused' },
    '11': { text: 'Пауза', class: 'status-paused' }
};

// Типы медиакампаний
const MEDIA_TYPE_MAP = {
    '1': 'По дням',
    '2': 'По просмотрам'
};

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initTabs();
    initFilters();
    initStatusTabs();
    loadPromotionCampaigns();

    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            if (currentTab === 'promotion') {
                loadPromotionCampaigns();
            } else {
                loadMediaCampaigns();
            }
        });
    }

    const exportBtn = document.getElementById('exportBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportToCSV);
    }
});

// Инициализация вкладок статусов
function initStatusTabs() {
    const statusTabs = document.querySelectorAll('.status-tab');
    
    // Сначала сбрасываем все активные классы
    statusTabs.forEach(tab => tab.classList.remove('active'));
    
    // Устанавливаем активную вкладку согласно currentStatusFilter
    const activeTab = document.querySelector(`.status-tab[data-status="${currentStatusFilter}"]`);
    if (activeTab) {
        activeTab.classList.add('active');
    }
    
    // Добавляем обработчики кликов
    statusTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            statusTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            currentStatusFilter = this.dataset.status;
            filterAndRenderCampaigns();
        });
    });
}

// Инициализация вкладок
function initTabs() {
    const tabs = document.querySelectorAll('.tab');
    if (tabs.length > 0) {
        tabs.forEach(tab => {
            tab.addEventListener('click', function() {
                const tabName = this.dataset.tab;
                switchTab(tabName);
            });
        });
    }
}

function switchTab(tabName) {
    currentTab = tabName;

    // Обновляем активные вкладки
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });

    // Показываем соответствующий контент
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    const tabElement = document.getElementById(`${tabName}Tab`);
    if (tabElement) {
        tabElement.classList.add('active');
    }

    // Загружаем данные если нужно
    if (tabName === 'promotion' && promotionCampaigns.length === 0) {
        loadPromotionCampaigns();
    } else if (tabName === 'media' && mediaCampaigns.length === 0) {
        loadMediaCampaigns();
    }
}

// Инициализация фильтров
function initFilters() {
    const statusFilter = document.getElementById('statusFilter');
    const paymentTypeFilter = document.getElementById('paymentTypeFilter');
    const searchInput = document.getElementById('searchInput');
    const mediaStatusFilter = document.getElementById('mediaStatusFilter');
    const mediaTypeFilter = document.getElementById('mediaTypeFilter');

    if (statusFilter) statusFilter.addEventListener('change', filterPromotionCampaigns);
    if (paymentTypeFilter) paymentTypeFilter.addEventListener('change', filterPromotionCampaigns);
    if (searchInput) searchInput.addEventListener('input', filterPromotionCampaigns);
    if (mediaStatusFilter) mediaStatusFilter.addEventListener('change', filterMediaCampaigns);
    if (mediaTypeFilter) mediaTypeFilter.addEventListener('change', filterMediaCampaigns);
}

// Загрузка кампаний продвижения
async function loadPromotionCampaigns() {
    showLoading(true);
    hideError();
    
    try {
        const response = await fetch('/campaigns/adverts');
        if (!response.ok) {
            throw new Error(`Ошибка HTTP: ${response.status}`);
        }
        
        promotionCampaigns = await response.json();
        updatePromotionStats();
        filterPromotionCampaigns();
    } catch (error) {
        showError(`Ошибка загрузки кампаний: ${error.message}`);
    } finally {
        showLoading(false);
    }
}

// Загрузка медиакампаний
async function loadMediaCampaigns() {
    showLoading(true);
    hideError();
    
    try {
        const status = document.getElementById('mediaStatusFilter').value;
        const type = document.getElementById('mediaTypeFilter').value;
        
        let url = '/campaigns/media?';
        if (status) url += `status=${status}&`;
        if (type) url += `type=${type}&`;
        
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Ошибка HTTP: ${response.status}`);
        }
        
        mediaCampaigns = await response.json();
        updateMediaStats();
        renderMediaCampaigns(mediaCampaigns);
    } catch (error) {
        showError(`Ошибка загрузки медиакампаний: ${error.message}`);
    } finally {
        showLoading(false);
    }
}

// Обновление статистики продвижения
function updatePromotionStats() {
    const total = promotionCampaigns.length;
    const active = promotionCampaigns.filter(c => c.status === 9).length;
    const paused = promotionCampaigns.filter(c => c.status === 11).length;
    const stopped = promotionCampaigns.filter(c => STATUS_GROUPS.stopped.includes(c.status)).length;

    const totalEl = document.getElementById('totalCount');
    const activeEl = document.getElementById('activeCount');
    const pausedEl = document.getElementById('pausedCount');
    const stoppedEl = document.getElementById('stoppedCount');

    if (totalEl) totalEl.textContent = total;
    if (activeEl) activeEl.textContent = active;
    if (pausedEl) pausedEl.textContent = paused;
    if (stoppedEl) stoppedEl.textContent = stopped;

    filterAndRenderCampaigns();
}

// Фильтрация и отображение кампаний по статусу
function filterAndRenderCampaigns() {
    let filtered = promotionCampaigns;

    // Применяем фильтр по статусу
    if (currentStatusFilter !== 'all' && STATUS_GROUPS[currentStatusFilter]) {
        filtered = promotionCampaigns.filter(c =>
            STATUS_GROUPS[currentStatusFilter].includes(c.status)
        );
    }

    // Обновляем визуальное состояние вкладок
    document.querySelectorAll('.status-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.status === currentStatusFilter);
    });

    renderPromotionCampaigns(filtered);
}

// Фильтрация кампаний продвижения (оставлено для совместимости)
function filterPromotionCampaigns() {
    filterAndRenderCampaigns();
}

// Фильтрация медиакампаний
function filterMediaCampaigns() {
    loadMediaCampaigns();
}

// Рендеринг кампаний продвижения
function renderPromotionCampaigns(campaigns) {
    const container = document.getElementById('campaignsContainer');
    if (!container) return;

    if (campaigns.length === 0) {
        container.innerHTML = '<div class="error-message">Кампании не найдены</div>';
        return;
    }

    container.innerHTML = campaigns.map(campaign => {
        const statusInfo = PROMOTION_STATUS_MAP[campaign.status] || { text: campaign.status, class: '' };
        const created = campaign.timestamps.created ? new Date(campaign.timestamps.created).toLocaleDateString('ru-RU') : '-';
        const started = campaign.timestamps.started ? new Date(campaign.timestamps.started).toLocaleDateString('ru-RU') : '-';

        return `
            <div class="campaign-card" data-id="${campaign.id}" onclick="window.location.href='/campaign/${campaign.id}'" style="cursor: pointer;">
                <div class="campaign-card-header">
                    <div class="campaign-card-title">
                        <div class="campaign-id">ID: ${campaign.id}</div>
                        <div class="campaign-name">${escapeHtml(campaign.settings.name)}</div>
                    </div>
                    <span class="campaign-status ${statusInfo.class}">${statusInfo.text}</span>
                </div>
                <div class="campaign-info">
                    <div>
                        <span class="info-label">Тип ставок:</span>
                        <span class="info-value">${campaign.bid_type === 'manual' ? 'Ручная' : 'Единая'}</span>
                    </div>
                    <div>
                        <span class="info-label">Оплата:</span>
                        <span class="info-value">${campaign.settings.payment_type === 'cpm' ? 'CPM' : 'CPC'}</span>
                    </div>
                    <div>
                        <span class="info-label">Товаров:</span>
                        <span class="info-value">${campaign.nm_settings.length}</span>
                    </div>
                    <div>
                        <span class="info-label">Создана:</span>
                        <span class="info-value">${created}</span>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Переход к кампании
function goToCampaign(campaignId) {
    window.location.href = `/campaign/${campaignId}`;
}

// Рендеринг медиакампаний
function renderMediaCampaigns(campaigns) {
    const tbody = document.getElementById('mediaCampaignsTableBody');
    
    if (campaigns.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #666;">Медиакампании не найдены</td></tr>';
        return;
    }
    
    tbody.innerHTML = campaigns.map(campaign => {
        const statusInfo = MEDIA_STATUS_MAP[campaign.status] || { text: campaign.status, class: '' };
        const typeText = MEDIA_TYPE_MAP[campaign.type] || campaign.type;
        const created = new Date(campaign.createTime).toLocaleDateString('ru-RU');
        
        return `
            <tr>
                <td>${campaign.advertId}</td>
                <td><strong>${escapeHtml(campaign.name)}</strong></td>
                <td>${escapeHtml(campaign.brand)}</td>
                <td>${typeText}</td>
                <td><span class="campaign-status ${statusInfo.class}">${statusInfo.text}</span></td>
                <td>${created}</td>
            </tr>
        `;
    }).join('');
}

// Экспорт в CSV
function exportToCSV() {
    let csv = '';
    let filename = '';
    
    if (currentTab === 'promotion') {
        csv = 'ID,Название,Статус,Тип ставок,Оплата,Товаров,Создана,Запущена\n';
        csv += promotionCampaigns.map(c => {
            const statusInfo = PROMOTION_STATUS_MAP[c.status] || { text: c.status };
            const created = c.timestamps.created ? new Date(c.timestamps.created).toISOString().split('T')[0] : '';
            const started = c.timestamps.started ? new Date(c.timestamps.started).toISOString().split('T')[0] : '';
            return `${c.id},"${c.settings.name.replace(/"/g, '""')}",${statusInfo.text},${c.bid_type},${c.settings.payment_type},${c.nm_settings.length},${created},${started}`;
        }).join('\n');
        filename = 'promotion_campaigns.csv';
    } else {
        csv = 'ID,Название,Бренд,Тип,Статус,Дата создания\n';
        csv += mediaCampaigns.map(c => {
            const statusInfo = MEDIA_STATUS_MAP[c.status] || { text: c.status };
            const created = new Date(c.createTime).toISOString().split('T')[0];
            return `${c.advertId},"${c.name.replace(/"/g, '""')}",${c.brand},${c.type},${statusInfo.text},${created}`;
        }).join('\n');
        filename = 'media_campaigns.csv';
    }
    
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
}

// Утилиты
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
