// auth.js - Аутентификация пользователей

document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const registerBtn = document.getElementById('registerBtn');
    const registerModal = document.getElementById('registerModal');
    const modalClose = document.querySelector('.modal-close');
    const registerForm = document.getElementById('registerForm');

    // Вход пользователя
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const username = document.getElementById('username').value.trim();
            
            try {
                const response = await fetch('/auth/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ username })
                });

                const data = await response.json();

                if (response.ok) {
                    showSuccess('Вход выполнен успешно! Перенаправление...');
                    setTimeout(() => {
                        window.location.href = '/profile';
                    }, 1000);
                } else {
                    showError(data.detail || 'Ошибка входа');
                }
            } catch (error) {
                showError('Ошибка подключения к серверу');
                console.error('Login error:', error);
            }
        });
    }

    // Открытие модального окна регистрации
    if (registerBtn && registerModal) {
        registerBtn.addEventListener('click', function() {
            registerModal.classList.remove('hidden');
        });
    }

    // Закрытие модального окна
    if (modalClose && registerModal) {
        modalClose.addEventListener('click', function() {
            registerModal.classList.add('hidden');
        });

        // Закрытие по клику вне окна
        registerModal.addEventListener('click', function(e) {
            if (e.target === registerModal) {
                registerModal.classList.add('hidden');
            }
        });
    }

    // Регистрация пользователя
    if (registerForm) {
        registerForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const username = document.getElementById('reg_username').value.trim();
            const email = document.getElementById('reg_email').value.trim();
            const token = document.getElementById('reg_token').value.trim();

            try {
                // Сначала создаём пользователя
                const userResponse = await fetch('/api/users', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ username, email })
                });

                const userData = await userResponse.json();

                if (!userResponse.ok) {
                    throw new Error(userData.detail || 'Ошибка регистрации пользователя');
                }

                // Затем создаём токен для пользователя
                const tokenResponse = await fetch(`/api/users/${userData.id}/tokens`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ 
                        token, 
                        description: 'Токен при регистрации' 
                    })
                });

                const tokenData = await tokenResponse.json();

                if (!tokenResponse.ok) {
                    throw new Error(tokenData.detail || 'Ошибка сохранения токена');
                }

                // Теперь автоматически входим
                const loginResponse = await fetch('/auth/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ username })
                });

                if (loginResponse.ok) {
                    showSuccess('Регистрация успешна! Перенаправление...');
                    setTimeout(() => {
                        window.location.href = '/profile';
                    }, 1000);
                }
            } catch (error) {
                showError(error.message || 'Ошибка регистрации');
                console.error('Register error:', error);
            }
        });
    }

    // Проверка есть ли уже активная сессия
    checkExistingSession();
});

async function checkExistingSession() {
    try {
        const response = await fetch('/auth/me');
        if (response.ok) {
            // Уже авторизован
            window.location.href = '/profile';
        }
    } catch (error) {
        console.error('Auth check error:', error);
    }
}

function showError(message) {
    const container = document.getElementById('errorContainer');
    container.textContent = message;
    container.classList.remove('hidden');
    setTimeout(() => {
        container.classList.add('hidden');
    }, 5000);
}

function showSuccess(message) {
    const container = document.getElementById('successContainer');
    container.textContent = message;
    container.classList.remove('hidden');
    setTimeout(() => {
        container.classList.add('hidden');
    }, 3000);
}
