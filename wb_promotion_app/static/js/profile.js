// profile.js - Личный кабинет пользователя

let currentUser = null;
let userTokens = [];

document.addEventListener('DOMContentLoaded', function() {
    loadUserProfile();
    loadUserTokens();
    
    // Обработчики кнопок
    const addTokenBtn = document.getElementById('addTokenBtn');
    const editTokenBtn = document.getElementById('editTokenBtn');
    const deleteTokenBtn = document.getElementById('deleteTokenBtn');
    const tokenForm = document.getElementById('tokenForm');
    
    if (addTokenBtn) {
        addTokenBtn.addEventListener('click', function() {
            document.getElementById('tokenFormContainer').classList.remove('hidden');
            document.getElementById('tokenErrorContainer').classList.add('hidden');
        });
    }
    
    if (editTokenBtn) {
        editTokenBtn.addEventListener('click', function() {
            document.getElementById('tokenFormContainer').classList.remove('hidden');
            document.getElementById('tokenSavedContainer').classList.add('hidden');
        });
    }
    
    if (deleteTokenBtn) {
        deleteTokenBtn.addEventListener('click', deleteToken);
    }
    
    if (tokenForm) {
        tokenForm.addEventListener('submit', saveToken);
    }
});

async function loadUserProfile() {
    try {
        const response = await fetch('/api/auth/me');
        if (!response.ok) {
            window.location.href = '/login';
            return;
        }
        
        currentUser = await response.json();
        
        // Заполняем данные пользователя
        document.getElementById('username').textContent = currentUser.username;
        document.getElementById('email').textContent = currentUser.email || 'Не указан';
        
        if (currentUser.created_at) {
            const date = new Date(currentUser.created_at);
            document.getElementById('created_at').textContent = date.toLocaleDateString('ru-RU', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
        }
        
        // Проверяем наличие токена
        checkTokenStatus();
        
    } catch (error) {
        console.error('Error loading profile:', error);
        window.location.href = '/login';
    }
}

async function checkTokenStatus() {
    const statusContainer = document.getElementById('tokenStatus');
    const formContainer = document.getElementById('tokenFormContainer');
    const savedContainer = document.getElementById('tokenSavedContainer');
    const errorContainer = document.getElementById('tokenErrorContainer');
    
    statusContainer.innerHTML = '<div class="loading">Проверка токена...</div>';
    
    try {
        const response = await fetch('/api/auth/token');
        const data = await response.json();
        
        if (response.ok && data.has_token) {
            // Токен есть
            statusContainer.innerHTML = '';
            formContainer.classList.add('hidden');
            savedContainer.classList.remove('hidden');
            errorContainer.classList.add('hidden');
        } else {
            // Токена нет
            statusContainer.innerHTML = '';
            formContainer.classList.add('hidden');
            savedContainer.classList.add('hidden');
            errorContainer.classList.remove('hidden');
        }
    } catch (error) {
        console.error('Error checking token:', error);
        statusContainer.innerHTML = '';
        formContainer.classList.add('hidden');
        savedContainer.classList.add('hidden');
        errorContainer.classList.remove('hidden');
    }
}

async function saveToken(e) {
    e.preventDefault();
    
    const token = document.getElementById('api_token').value.trim();
    const messageContainer = document.getElementById('messageContainer');
    
    if (!token) {
        showMessage('Введите токен', 'error');
        return;
    }
    
    try {
        // Проверяем есть ли уже токен
        const checkResponse = await fetch('/api/auth/token');
        const checkData = await checkResponse.json();
        
        let response;
        let data;
        
        if (checkResponse.ok && checkData.has_token && checkData.token_id) {
            // Обновляем существующий
            response = await fetch(`/api/users/${currentUser.id}/tokens/${checkData.token_id}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ token })
            });
            data = await response.json();
        } else {
            // Создаём новый
            response = await fetch(`/api/users/${currentUser.id}/tokens`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    token,
                    description: 'Сохранён из личного кабинета'
                })
            });
            data = await response.json();
        }
        
        if (response.ok) {
            showMessage('Токен успешно сохранён!', 'success');
            document.getElementById('tokenFormContainer').classList.add('hidden');
            setTimeout(() => {
                checkTokenStatus();
                loadUserTokens();
            }, 1000);
        } else {
            showMessage(data.detail || 'Ошибка сохранения токена', 'error');
        }
    } catch (error) {
        console.error('Error saving token:', error);
        showMessage('Ошибка подключения к серверу', 'error');
    }
}

async function deleteToken() {
    if (!confirm('Вы уверены что хотите удалить токен? Приложение перестанет работать без токена.')) {
        return;
    }
    
    try {
        // Сначала получаем ID токена
        const checkResponse = await fetch('/api/auth/token');
        const checkData = await checkResponse.json();
        
        if (!checkData.token_id) {
            showMessage('Токен не найден', 'error');
            return;
        }
        
        const response = await fetch(`/api/users/${currentUser.id}/tokens/${checkData.token_id}`, {
            method: 'DELETE'
        });
        
        if (response.ok || response.status === 204) {
            showMessage('Токен удалён', 'success');
            setTimeout(() => {
                checkTokenStatus();
                loadUserTokens();
            }, 1000);
        } else {
            const data = await response.json();
            showMessage(data.detail || 'Ошибка удаления токена', 'error');
        }
    } catch (error) {
        console.error('Error deleting token:', error);
        showMessage('Ошибка подключения к серверу', 'error');
    }
}

async function loadUserTokens() {
    const tokensList = document.getElementById('tokensList');
    
    try {
        const response = await fetch(`/api/users/${currentUser.id}/tokens`);
        const tokens = await response.json();
        
        if (response.ok && tokens.length > 0) {
            userTokens = tokens;
            let html = '<div class="tokens-table">';
            html += '<table><thead><tr><th>ID</th><th>Описание</th><th>Статус</th><th>Создан</th><th>Действия</th></tr></thead><tbody>';
            
            tokens.forEach(token => {
                const statusClass = token.is_active ? 'status-active' : 'status-inactive';
                const statusText = token.is_active ? '✅ Активен' : '❌ Неактивен';
                const createdDate = new Date(token.created_at).toLocaleDateString('ru-RU');
                
                html += `<tr>
                    <td>${token.id}</td>
                    <td>${token.description || '—'}</td>
                    <td><span class="badge ${statusClass}">${statusText}</span></td>
                    <td>${createdDate}</td>
                    <td>
                        ${token.is_active ? `<button class="btn-small btn-danger" onclick="deactivateToken(${token.id})">Деактивировать</button>` : ''}
                        <button class="btn-small btn-danger" onclick="deleteTokenById(${token.id})">Удалить</button>
                    </td>
                </tr>`;
            });
            
            html += '</tbody></table></div>';
            tokensList.innerHTML = html;
        } else {
            tokensList.innerHTML = '<p class="empty-message">У вас пока нет сохранённых токенов</p>';
        }
    } catch (error) {
        console.error('Error loading tokens:', error);
        tokensList.innerHTML = '<p class="error-message">Ошибка загрузки списка токенов</p>';
    }
}

async function deactivateToken(tokenId) {
    try {
        const response = await fetch(`/api/users/${currentUser.id}/tokens/${tokenId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ is_active: false })
        });
        
        if (response.ok) {
            showMessage('Токен деактивирован', 'success');
            setTimeout(() => {
                loadUserTokens();
                checkTokenStatus();
            }, 1000);
        }
    } catch (error) {
        console.error('Error deactivating token:', error);
    }
}

async function deleteTokenById(tokenId) {
    if (!confirm('Вы уверены что хотите удалить этот токен?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/users/${currentUser.id}/tokens/${tokenId}`, {
            method: 'DELETE'
        });
        
        if (response.ok || response.status === 204) {
            showMessage('Токен удалён', 'success');
            setTimeout(() => {
                loadUserTokens();
                checkTokenStatus();
            }, 1000);
        }
    } catch (error) {
        console.error('Error deleting token:', error);
    }
}

function showMessage(message, type = 'info') {
    const container = document.getElementById('messageContainer');
    container.textContent = message;
    container.className = `message-container ${type}`;
    container.classList.remove('hidden');
    
    setTimeout(() => {
        container.classList.add('hidden');
    }, 5000);
}
