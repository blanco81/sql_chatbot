document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.querySelector('.chat-form');
    const chatHistory = document.getElementById('chatHistory');
    const inputField = document.querySelector('.chat-form input');

    // Auto-enfocar el campo de entrada
    if (inputField) inputField.focus();

    // Desplazarse al final del chat al cargar
    if (chatHistory) scrollToBottom();

    // Manejar envío del formulario
    if (chatForm) {
        chatForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const userInput = inputField.value.trim();
            if (!userInput) return;

            // Mostrar mensaje del usuario
            addMessage(userInput, 'user');
            
            // Mostrar indicador de carga
            const loadingId = addMessage('Pensando...', 'bot', true);
            
            // Enviar consulta al servidor
            try {
                const response = await fetch('/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `user_input=${encodeURIComponent(userInput)}`
                });
                
                if (!response.ok) throw new Error('Error en la respuesta');
                
                const html = await response.text();
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const botResponse = doc.querySelector('.bot-message').innerHTML;
                
                // Actualizar mensaje de carga con respuesta
                updateMessage(loadingId, botResponse);
                
            } catch (error) {
                console.error('Error:', error);
                updateMessage(loadingId, '<strong>Bot:</strong> Error al procesar tu solicitud');
            } finally {
                inputField.value = '';
                inputField.focus();
                scrollToBottom();
            }
        });
    }

    function addMessage(content, type, isTemp = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        messageDiv.innerHTML = type === 'user' 
            ? `<strong>Tú:</strong> ${content}`
            : `<strong>Bot:</strong> ${content}`;
        
        if (isTemp) messageDiv.id = 'temp-' + Date.now();
        chatHistory.appendChild(messageDiv);
        scrollToBottom();
        return messageDiv.id;
    }

    function updateMessage(id, newContent) {
        const message = document.getElementById(id);
        if (message) message.innerHTML = newContent;
    }

    function scrollToBottom() {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
});