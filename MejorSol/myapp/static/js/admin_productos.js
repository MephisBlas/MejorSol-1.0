// admin_productos.js - Funcionalidades para el módulo de productos

document.addEventListener('DOMContentLoaded', function() {
    initializeProductModule();
});

function initializeProductModule() {
    // Manejar envío de formularios de eliminación
    const deleteForms = document.querySelectorAll('.delete-form');
    deleteForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('¿Estás seguro de que deseas eliminar este producto? Esta acción no se puede deshacer.')) {
                e.preventDefault();
            }
        });
    });

    // Auto-ocultar mensajes después de 5 segundos
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateX(100%)';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });

    // Validación de formulario en tiempo real
    const productForm = document.querySelector('.product-form');
    if (productForm) {
        initializeFormValidation(productForm);
    }
}

function openModal(productId) {
    fetch(`/admin/productos/detalle/${productId}/`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Error al cargar los detalles del producto');
            }
            return response.text();
        })
        .then(html => {
            document.getElementById('modalBody').innerHTML = html;
            document.getElementById('productModal').style.display = 'block';
            document.body.style.overflow = 'hidden'; // Prevenir scroll del body
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('modalBody').innerHTML = `
                <div class="alert alert-error">
                    <i class="fas fa-exclamation-triangle"></i>
                    Error al cargar los detalles del producto.
                </div>
            `;
            document.getElementById('productModal').style.display = 'block';
        });
}

function closeModal() {
    document.getElementById('productModal').style.display = 'none';
    document.body.style.overflow = 'auto'; // Restaurar scroll del body
}

function initializeFormValidation(form) {
    const skuInput = form.querySelector('#id_sku');
    const precioInput = form.querySelector('#id_precio');
    const stockInput = form.querySelector('#id_stock');
    const stockMinimoInput = form.querySelector('#id_stock_minimo');

    // Validar SKU único mientras se escribe
    if (skuInput) {
        let skuTimeout;
        skuInput.addEventListener('input', function() {
            clearTimeout(skuTimeout);
            skuTimeout = setTimeout(() => {
                validateSKU(this.value);
            }, 500);
        });
    }

    // Validar que el precio sea positivo
    if (precioInput) {
        precioInput.addEventListener('blur', function() {
            const value = parseFloat(this.value);
            if (value < 0) {
                showFieldError(this, 'El precio no puede ser negativo');
            } else {
                clearFieldError(this);
            }
        });
    }

    // Validar que el stock no sea negativo
    if (stockInput) {
        stockInput.addEventListener('blur', function() {
            const value = parseInt(this.value);
            if (value < 0) {
                showFieldError(this, 'El stock no puede ser negativo');
            } else {
                clearFieldError(this);
            }
        });
    }

    // Validar que el stock mínimo no sea negativo
    if (stockMinimoInput) {
        stockMinimoInput.addEventListener('blur', function() {
            const value = parseInt(this.value);
            if (value < 0) {
                showFieldError(this, 'El stock mínimo no puede ser negativo');
            } else {
                clearFieldError(this);
            }
        });
    }
}

function validateSKU(sku) {
    if (!sku) return;

    const form = document.querySelector('.product-form');
    const productId = form ? form.querySelector('[name="product_id"]')?.value : null;
    const url = `/admin/validate-sku/?sku=${encodeURIComponent(sku)}${productId ? `&exclude=${productId}` : ''}`;

    fetch(url)
        .then(response => response.json())
        .then(data => {
            const skuInput = document.querySelector('#id_sku');
            if (!data.available) {
                showFieldError(skuInput, 'Este SKU ya está en uso');
            } else {
                clearFieldError(skuInput);
            }
        })
        .catch(error => console.error('Error validando SKU:', error));
}

function showFieldError(field, message) {
    clearFieldError(field);
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-text';
    errorDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
    
    field.style.borderColor = '#dc3545';
    field.parentNode.appendChild(errorDiv);
}

function clearFieldError(field) {
    const existingError = field.parentNode.querySelector('.error-text');
    if (existingError) {
        existingError.remove();
    }
    field.style.borderColor = '';
}

// Cerrar modal al hacer click fuera o presionar ESC
window.onclick = function(event) {
    const modal = document.getElementById('productModal');
    if (event.target === modal) {
        closeModal();
    }
}

document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeModal();
    }
});

// Exportar funciones para uso global
window.openModal = openModal;
window.closeModal = closeModal;