/**
 * Sistema de gestión de saldo para juegos de casino
 * Versión 1.0
 */

function setupBalanceSystem() {
    // Obtener el elemento que muestra el saldo
    const balanceElements = document.querySelectorAll('#saldo-usuario');
    let currentBalance = 0;
    
    // Inicializar el saldo desde el elemento HTML
    if (balanceElements.length > 0) {
        currentBalance = parseInt(balanceElements[0].textContent) || 0;
    }
    
    // Función para actualizar todos los elementos que muestran el saldo
    function updateDisplayedBalance(newBalance) {
        balanceElements.forEach(element => {
            element.textContent = newBalance;
        });
    }
    
    // Función para mostrar notificaciones
    function showNotification(message, isPositive = true) {
        // Crear elemento de notificación
        const notification = document.createElement('div');
        notification.className = 'balance-notification';
        notification.style.color = 'white';
        notification.style.borderLeftColor = isPositive ? '#4CAF50' : '#F44336';
        notification.textContent = message;
        
        // Añadir al DOM
        document.body.appendChild(notification);
        
        // Eliminar después de 3 segundos
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 500);
        }, 3000);
    }
    
    // Función para actualizar el saldo en el servidor
    async function updateBalanceOnServer(amount) {
        try {
            const response = await fetch('/actualizar_saldo', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    cambio: amount
                }),
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Error al actualizar saldo');
            }
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error en la comunicación con el servidor:', error);
            throw error;
        }
    }
    
    // Función para actualizar el saldo (ganancia o pérdida)
    async function updateBalance(amount, isWin = true) {
        try {
            // Validar que el saldo no quede negativo en caso de pérdida
            if (!isWin && Math.abs(amount) > currentBalance) {
                showNotification('Saldo insuficiente', false);
                return false;
            }
            
            // Actualizar en el servidor
            const result = await updateBalanceOnServer(amount);
            
            if (result.success) {
                // Actualizar saldo local
                currentBalance = result.nuevo_saldo;
                updateDisplayedBalance(currentBalance);
                
                // Mostrar notificación
                const message = isWin 
                    ? `¡Ganaste ${amount}!` 
                    : `Apostaste ${Math.abs(amount)}`;
                showNotification(message, isWin);
                
                return true;
            } else {
                showNotification(result.error || 'Error al actualizar saldo', false);
                return false;
            }
        } catch (error) {
            showNotification('Error de conexión', false);
            console.error(error);
            return false;
        }
    }
    
    // Obtener saldo actual
    function getBalance() {
        return currentBalance;
    }
    
    // Verificar si hay saldo suficiente para una apuesta
    function hasSufficientBalance(amount) {
        return currentBalance >= amount;
    }
    
    // Devolver API pública
    return {
        updateBalance,
        getBalance,
        hasSufficientBalance,
        showNotification
    };
}