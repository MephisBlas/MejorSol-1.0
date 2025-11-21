document.addEventListener('DOMContentLoaded', () => {
    
    // 1. Listener para el Widget de Dialogflow (<df-messenger>)
    // Este evento se dispara cuando el chat de Google carga completamente
    window.addEventListener('dfMessengerLoaded', function (event) {
        console.log('Chatbot Sieer cargado y listo.');
        
        const dfMessenger = document.querySelector('df-messenger');
        if (dfMessenger) {
            // Opcional: Puedes forzar que el chat se abra solo o envíe un saludo
            // dfMessenger.renderCustomText('¡Hola! ¿En qué puedo ayudarte hoy?');
        }
    });

    // 2. Manejo de eventos de envío (Opcional, para logs)
    window.addEventListener('df-request-sent', function (event) {
        console.log('Solicitud enviada al bot:', event.detail);
    });
});

// 3. Función para obtener el CSRF Token 
// (Útil si necesitas hacer otras peticiones AJAX en el futuro)
function getCSRFToken() {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Busca la cookie que empieza con csrftoken=
            if (cookie.substring(0, 10) === ('csrftoken=')) {
                cookieValue = decodeURIComponent(cookie.substring(10));
                break;
            }
        }
    }
    return cookieValue;
}