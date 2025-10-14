// script.js - Funcionalidades para responsividad y menú móvil

document.addEventListener('DOMContentLoaded', function() {
    // Elementos del DOM
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const nav = document.querySelector('.nav-centered');
    const authButtons = document.querySelector('.auth-buttons');
    const header = document.querySelector('.header');

    // Menú móvil
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function() {
            const isActive = nav.classList.contains('active');
            
            // Cerrar todo primero
            nav.classList.remove('active');
            authButtons.classList.remove('active');
            
            // Abrir menú de navegación
            if (!isActive) {
                nav.classList.add('active');
            }
            
            // Cambiar ícono
            this.classList.toggle('fa-bars');
            this.classList.toggle('fa-times');
        });
    }

    // Cerrar menús al hacer clic fuera
    document.addEventListener('click', function(event) {
        if (!event.target.closest('.header-content')) {
            nav.classList.remove('active');
            authButtons.classList.remove('active');
            if (mobileMenuToggle) {
                mobileMenuToggle.classList.add('fa-bars');
                mobileMenuToggle.classList.remove('fa-times');
            }
        }
    });

    // Smooth scrolling para enlaces internos
    const internalLinks = document.querySelectorAll('a[href^="#"]');
    
    internalLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            
            if (href !== '#' && href !== '') {
                e.preventDefault();
                
                const targetId = href;
                const targetElement = document.querySelector(targetId);
                
                if (targetElement) {
                    const headerHeight = header.offsetHeight;
                    const targetPosition = targetElement.offsetTop - headerHeight;
                    
                    // Cerrar menús móviles
                    nav.classList.remove('active');
                    authButtons.classList.remove('active');
                    if (mobileMenuToggle) {
                        mobileMenuToggle.classList.add('fa-bars');
                        mobileMenuToggle.classList.remove('fa-times');
                    }
                    
                    window.scrollTo({
                        top: targetPosition,
                        behavior: 'smooth'
                    });
                }
            }
        });
    });

    // Header sticky on scroll
    function stickyHeader() {
        if (window.scrollY > 100) {
            header.classList.add('sticky');
        } else {
            header.classList.remove('sticky');
        }
    }

    window.addEventListener('scroll', stickyHeader);

    // Manejar redimensionamiento de ventana
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            nav.classList.remove('active');
            authButtons.classList.remove('active');
            if (mobileMenuToggle) {
                mobileMenuToggle.classList.add('fa-bars');
                mobileMenuToggle.classList.remove('fa-times');
            }
        }
    });

    // Efectos de aparición para elementos al hacer scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observar elementos para animaciones
    const animatedElements = document.querySelectorAll('.service-card, .project-card');
    animatedElements.forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        element.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(element);
    });
});

// Función para mostrar/ocultar botones de auth en móvil
function toggleAuthButtons() {
    const authButtons = document.querySelector('.auth-buttons');
    const nav = document.querySelector('.nav-centered');
    
    if (authButtons) {
        authButtons.classList.toggle('active');
        nav.classList.remove('active');
    }
}