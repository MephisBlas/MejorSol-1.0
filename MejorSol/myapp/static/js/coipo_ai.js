document.getElementById("coipo-chat-launcher").onclick = () => {
    const win = document.getElementById("coipo-chat-window");
    win.style.display = win.style.display === "flex" ? "none" : "flex";
};

async function sendCoipoMessage() {
    const input = document.getElementById("coipo-chat-input");
    const text = input.value.trim();

    if (!text) return;

    appendMessage("user", text);

    input.value = "";

    const response = await fetch(""/api/chatbot-dialogflow/"", {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken()
        },
        body: JSON.stringify({ message: text })
    });

    const data = await response.json();

    appendMessage("bot", data.response || "No pude procesar eso.");
}

function appendMessage(sender, message) {
    const box = document.getElementById("coipo-chat-messages");
    const div = document.createElement("div");

    div.className = sender === "user" ? "msg-user" : "msg-bot";
    div.innerText = message;

    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
}

document.getElementById("coipo-chat-send").onclick = sendCoipoMessage;

document.getElementById("coipo-chat-input").addEventListener("keypress", function(e) {
    if (e.key === "Enter") sendCoipoMessage();
});

// para manejar CSRF correctamente
function getCSRFToken() {
    let cookieValue = null;
    const cookies = document.cookie.split(";");

    for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith("csrftoken=")) {
            cookieValue = cookie.substring("csrftoken=".length);
            break;
        }
    }
    return cookieValue;
}

