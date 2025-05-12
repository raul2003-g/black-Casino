document.addEventListener('DOMContentLoaded', function() {
    // Manejo del formulario de registro
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Validación de contraseña
            const password = this.querySelector('input[name="password"]').value;
            const confirmPassword = this.querySelector('input[name="confirm_password"]').value;
            
            if (password !== confirmPassword) {
                showAuthError('Las contraseñas no coinciden');
                return;
            }
            
            const formData = new FormData(this);
            
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest' // Para identificar peticiones AJAX
                }
            })
            .then(response => {
                // Verificar si la respuesta es JSON
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    return response.json();
                }
                
                if (response.redirected) {
                    window.location.href = response.url;
                    return;
                }
                
                return response.text().then(text => {
                    throw new Error('Respuesta inesperada del servidor');
                });
            })
            .then(data => {
                if (data && data.error) {
                    showAuthError(data.error);
                } else if (data && data.redirect) {
                    window.location.href = data.redirect;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAuthError('Error en el servidor. Por favor intenta nuevamente.');
            });
        });
    }

    // Función para mostrar errores
    function showAuthError(message) {
        const errorContainer = document.querySelector('.auth-error');
        if (errorContainer) {
            errorContainer.textContent = message;
            errorContainer.style.display = 'block';
            setTimeout(() => {
                errorContainer.style.display = 'none';
            }, 5000);
        }
    }
});