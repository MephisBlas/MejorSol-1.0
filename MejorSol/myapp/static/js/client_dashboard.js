// client_dashboard.js - Versión responsiva

document.addEventListener('DOMContentLoaded', function() {
    // Elementos del DOM
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const mobileNavOverlay = document.getElementById('mobileNavOverlay');
    const mobileCloseBtn = document.getElementById('mobileCloseBtn');
    const navTabs = document.querySelectorAll('.nav-tab');
    const mobileNavTabs = document.querySelectorAll('.mobile-nav-tab');
    const tabContents = document.querySelectorAll('.tab-content');
    
    // Abrir menú móvil
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function() {
            mobileNavOverlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        });
    }
    
    // Cerrar menú móvil
    if (mobileCloseBtn) {
        mobileCloseBtn.addEventListener('click', closeMobileMenu);
    }
    
    // Cerrar menú al hacer clic fuera
    if (mobileNavOverlay) {
        mobileNavOverlay.addEventListener('click', function(e) {
            if (e.target === mobileNavOverlay) {
                closeMobileMenu();
            }
        });
    }
    
    // Cerrar menú con Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeMobileMenu();
        }
    });
    
    function closeMobileMenu() {
        mobileNavOverlay.classList.remove('active');
        document.body.style.overflow = '';
    }
    
    // Navegación por tabs (escritorio)
    navTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            switchTab(this.getAttribute('data-tab'));
        });
    });
    
    // Navegación por tabs (móvil)
    mobileNavTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');
            switchTab(targetTab);
            closeMobileMenu();
        });
    });
    
    function switchTab(targetTab) {
        // Remove active class from all tabs and contents
        navTabs.forEach(t => t.classList.remove('active'));
        mobileNavTabs.forEach(t => t.classList.remove('active'));
        tabContents.forEach(c => c.classList.remove('active'));
        
        // Add active class to current tab and content
        const activeNavTab = document.querySelector(`.nav-tab[data-tab="${targetTab}"]`);
        const activeMobileTab = document.querySelector(`.mobile-nav-tab[data-tab="${targetTab}"]`);
        const activeContent = document.getElementById(`${targetTab}-tab`);
        
        if (activeNavTab) activeNavTab.classList.add('active');
        if (activeMobileTab) activeMobileTab.classList.add('active');
        if (activeContent) activeContent.classList.add('active');
        
        // Scroll to top cuando cambias de tab en móvil
        if (window.innerWidth <= 768) {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }
    
    // Efectos hover mejorados para dispositivos táctiles
    const interactiveElements = document.querySelectorAll('.service-card, .product-card, .document-item, .btn');
    
    interactiveElements.forEach(element => {
        element.addEventListener('touchstart', function() {
            this.classList.add('touch-active');
        });
        
        element.addEventListener('touchend', function() {
            this.classList.remove('touch-active');
        });
    });
    
    // Optimización de rendimiento para scroll
    let scrollTimer;
    window.addEventListener('scroll', function() {
        if (!document.body.classList.contains('disable-hover')) {
            document.body.classList.add('disable-hover');
        }
        
        clearTimeout(scrollTimer);
        scrollTimer = setTimeout(function() {
            document.body.classList.remove('disable-hover');
        }, 500);
    });
    
    // Carga perezosa de imágenes (si las agregas en el futuro)
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
    
    // Manejo de redimensionamiento
    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            // Ajustes específicos para cambios de tamaño
            if (window.innerWidth > 768) {
                closeMobileMenu();
            }
        }, 250);
    });
    
    // Feedback táctil mejorado
    document.addEventListener('touchstart', function() {}, { passive: true });
    
    console.log('Panel del cliente cargado - Versión responsiva');
});

// Clase para manejar estados de carga
class ClientDashboard {
    constructor() {
        this.isLoading = false;
    }
    
    showLoading() {
        this.isLoading = true;
        // Aquí puedes agregar un spinner de carga
    }
    
    hideLoading() {
        this.isLoading = false;
        // Ocultar spinner
    }
    
    // Método para cargar datos dinámicamente
    async loadTabData(tabName) {
        if (this.isLoading) return;
        
        this.showLoading();
        
        try {
            // Simular carga de datos
            await new Promise(resolve => setTimeout(resolve, 500));
            console.log(`Datos cargados para: ${tabName}`);
        } catch (error) {
            console.error('Error cargando datos:', error);
        } finally {
            this.hideLoading();
        }
    }
}

// Inicializar la aplicación
const clientApp = new ClientDashboard();

