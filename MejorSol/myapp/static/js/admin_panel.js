// admin_panel.js - Funcionalidades del panel administrativo

document.addEventListener('DOMContentLoaded', function() {
    // ===== TOGGLE MENU MÓVIL =====
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.querySelector('.admin-sidebar');
    
    if (menuToggle) {
        menuToggle.addEventListener('click', function() {
            sidebar.classList.toggle('active');
        });
    }
    
    // ===== CERRAR MENU AL HACER CLIC EN UN LINK =====
    const navLinks = document.querySelectorAll('.nav-item a');
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth <= 768) {
                sidebar.classList.remove('active');
            }
        });
    });
    
    // ===== NOTIFICACIONES =====
    const notificationBell = document.querySelector('.notification-bell');
    if (notificationBell) {
        notificationBell.addEventListener('click', function() {
            showNotification('Tienes 3 notificaciones pendientes', 'info');
        });
    }
    
    // ===== BOTONES DE ACCIÓN =====
    const actionButtons = document.querySelectorAll('.action-card .btn');
    actionButtons.forEach(button => {
        button.addEventListener('click', function() {
            const card = this.closest('.action-card');
            const actionName = card.querySelector('h4').textContent;
            
            // Simular acción
            showNotification(`Iniciando: ${actionName}`, 'success');
        });
    });
    
    // ===== SIMULAR DATOS EN TIEMPO REAL =====
    function updateStats() {
        const stats = document.querySelectorAll('.stat-info h3');
        if (stats.length > 0) {
            // Simular cambios pequeños en las estadísticas
            stats.forEach(stat => {
                const currentText = stat.textContent;
                const currentValue = parseFloat(currentText.replace(/[^0-9.]/g, ''));
                if (!isNaN(currentValue)) {
                    const change = (Math.random() - 0.5) * 0.1; // ±5%
                    const newValue = currentValue * (1 + change);
                    
                    if (currentText.includes('$')) {
                        stat.textContent = `$ ${Math.round(newValue).toLocaleString()}`;
                    } else {
                        stat.textContent = Math.round(newValue).toLocaleString();
                    }
                }
            });
        }
    }
    
    // Actualizar estadísticas cada 30 segundos
    setInterval(updateStats, 30000);
    
    // ===== NOTIFICACIONES TOAST =====
    function showNotification(message, type = 'info') {
        // Verificar si ya existe una notificación
        const existingNotification = document.querySelector('.notification-toast');
        if (existingNotification) {
            existingNotification.remove();
        }
        
        const notification = document.createElement('div');
        notification.className = `notification-toast ${type}`;
        notification.innerHTML = `
            <div class="toast-icon">
                <i class="fas fa-${getIconForType(type)}"></i>
            </div>
            <div class="toast-message">${message}</div>
            <button class="toast-close"><i class="fas fa-times"></i></button>
        `;
        
        // Estilos del toast
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--card-bg);
            border: var(--border-glow);
            border-radius: 8px;
            padding: 1rem;
            display: flex;
            align-items: center;
            gap: 1rem;
            z-index: 10000;
            transform: translateX(100%);
            transition: transform 0.3s ease;
            max-width: 350px;
            backdrop-filter: blur(10px);
            ${type === 'success' ? 'border-color: var(--primary-green);' : ''}
            ${type === 'error' ? 'border-color: #ff4757;' : ''}
            ${type === 'warning' ? 'border-color: #ffa500;' : ''}
        `;
        
        document.body.appendChild(notification);
        
        // Animación de entrada
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Cerrar notificación
        const closeBtn = notification.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (document.body.contains(notification)) {
                    document.body.removeChild(notification);
                }
            }, 300);
        });
        
        // Auto-remover después de 5 segundos
        setTimeout(() => {
            if (document.body.contains(notification)) {
                notification.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    if (document.body.contains(notification)) {
                        document.body.removeChild(notification);
                    }
                }, 300);
            }
        }, 5000);
    }
    
    function getIconForType(type) {
        switch (type) {
            case 'success': return 'check-circle';
            case 'error': return 'exclamation-circle';
            case 'warning': return 'exclamation-triangle';
            default: return 'info-circle';
        }
    }
    
    // ===== ACTIVIDAD RECIENTE ANIMADA =====
    const activityItems = document.querySelectorAll('.activity-item');
    activityItems.forEach((item, index) => {
        item.style.opacity = '0';
        item.style.transform = 'translateX(-20px)';
        item.style.transition = `opacity 0.5s ease ${index * 0.1}s, transform 0.5s ease ${index * 0.1}s`;
        
        setTimeout(() => {
            item.style.opacity = '1';
            item.style.transform = 'translateX(0)';
        }, 100 + (index * 100));
    });
    
    console.log('Panel administrativo de SIEER Chile inicializado');
});