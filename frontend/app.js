const API_URL = "https://all-ai-1-ndsb.onrender.com";
let currentChatHistory = []; // Aici ținem minte mesajele din conversația curentă
let currentSessionId = null; // Ține minte în ce chat suntem

// Verificăm dacă suntem deja logați
window.onload = () => {
    if (localStorage.getItem("access_token")) {
        showChat();
    }
};

// Când se încarcă pagina, dacă avem token de logare, încărcăm direct sesiunile
document.addEventListener("DOMContentLoaded", () => {
    const token = localStorage.getItem("access_token");
    if (token) {
        loadSessions();
    }
});

// Funcția pentru LOGARE (Intră în contul existent)
async function login() {
    const user = document.getElementById("username").value;
    const pass = document.getElementById("password").value;

    if (!user || !pass) {
        alert("Introdu username și parola!");
        return;
    }

    try {
        const formData = new URLSearchParams();
        formData.append("username", user + "@test.com"); 
        formData.append("password", pass);

        const response = await fetch(`${API_URL}/api/auth/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: formData.toString()
        });

        if (response.ok) {
            const data = await response.json();
            localStorage.setItem("access_token", data.access_token);
            
            document.getElementById("auth-container").classList.add("hidden");
            document.getElementById("chat-container").classList.remove("hidden");
            
            showChat();
        } else {
            const errorData = await response.json();
            alert("Eroare la login: " + JSON.stringify(errorData));
        }
    } catch (error) {
        console.error("Eroare la login:", error);
    }
}
// Așa trebuie să arate funcția corectă: pur și simplu golește ecranul!
function createNewSession() {
    currentSessionId = null; // Îi spunem că nu mai suntem în niciun chat vechi
    currentChatHistory = []; // AI-ul primește amnezie
    document.getElementById("chat-box").innerHTML = ""; // Curățăm ecranul
    
    // ATÂT! Nu trimitem nicio cerere la server aici. 
    // Serverul va crea sesiunea abia când trimiți primul mesaj.
}
// Funcția pentru ÎNREGISTRARE (Creează un cont nou)
async function register() {
    const user = document.getElementById("username").value;
    const pass = document.getElementById("password").value;
    const msg = document.getElementById("auth-message");

    if (!user || !pass) {
        msg.innerText = "Te rog introdu username-ul și parola pentru noul cont.";
        return;
    }

    try {
        const response = await fetch(`${API_URL}/api/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: user, email: user + "@test.com", password: pass })
        });

        if (response.ok) {
            msg.innerText = "Cont creat cu succes! Acum te poți loga.";
            msg.style.color = "#10b981"; 
        } else {
            const data = await response.json();
            msg.innerText = data.detail || "Acest nume de utilizator există deja.";
            msg.style.color = "#ef4444"; 
        }
    } catch (error) {
        msg.innerText = "Eroare de conexiune la server.";
    }
}

function logout() {
    localStorage.removeItem("access_token");
    document.getElementById("chat-container").classList.add("hidden");
    document.getElementById("auth-container").classList.remove("hidden");
    document.getElementById("email").value = "";
    document.getElementById("password").value = "";
}

// Funcția care schimbă ecranele
function showChat() {
    document.getElementById("auth-container").classList.add("hidden");
    document.getElementById("chat-container").classList.remove("hidden");
    
    loadSessions(); 
    checkPaymentStatus();
    getCredits();
}

function handleEnter(event) {
    if (event.key === "Enter") sendMessage();
}

// --- FUNCȚII PENTRU SESIUNILE DE CHAT ---

// 1. Încarcă lista de sesiuni în bara din stânga (Designul tău cu Edit/Delete)
async function loadSessions() {
    const token = localStorage.getItem("access_token");
    if (!token) return;

    try {
        const response = await fetch(`${API_URL}/api/chat/sessions`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        const sessions = await response.json();
        const sessionsList = document.getElementById("sessions-list");
        sessionsList.innerHTML = "";

        sessions.forEach(session => {
            const li = document.createElement("li");
            li.className = "session-item";
            if (session.id === currentSessionId) {
                li.classList.add("active");
            }

            const titleSpan = document.createElement("span");
            titleSpan.className = "session-title";
            titleSpan.innerText = session.title;
            titleSpan.onclick = () => loadSessionHistory(session.id);

            const actionsDiv = document.createElement("div");
            actionsDiv.className = "session-actions";

            const editBtn = document.createElement("button");
            editBtn.title = "Redenumește";
            editBtn.innerText = "✏️";
            editBtn.onclick = (e) => {
                e.stopPropagation(); 
                renameChat(session.id, session.title);
            };

            const deleteBtn = document.createElement("button");
            deleteBtn.title = "Șterge";
            deleteBtn.innerText = "🗑️";
            deleteBtn.onclick = (e) => {
                e.stopPropagation(); 
                deleteChat(session.id);
            };

            actionsDiv.appendChild(editBtn);
            actionsDiv.appendChild(deleteBtn);
            li.appendChild(titleSpan);
            li.appendChild(actionsDiv);

            sessionsList.appendChild(li);
        });
    } catch (error) {
        console.error("Eroare la încărcarea sesiunilor:", error);
    }
}

// 2. Creează o conversație nouă
function createNewSession() {
    currentSessionId = null; // Resetăm ID-ul ca backend-ul să știe să facă una nouă
    currentChatHistory = []; // Golim memoria AI-ului
    document.getElementById("chat-box").innerHTML = ""; // Curățăm ecranul
    loadSessions(); // Reîmprospătăm meniul
}

// 3. Încarcă mesajele unei sesiuni vechi pe ecran
async function loadSessionHistory(sessionId) {
    const token = localStorage.getItem("access_token");
    if (!token) return;

    try {
        const response = await fetch(`${API_URL}/api/chat/session/${sessionId}`, {
            headers: { "Authorization": `Bearer ${token}` }
        });

        if (!response.ok) return;

        const messages = await response.json();
        const chatBox = document.getElementById("chat-box");
        chatBox.innerHTML = ""; 
        currentChatHistory = []; 

        messages.forEach(msg => {
            appendMessage(msg.content, msg.sender);
            
            const roleForHistory = msg.sender === "user" ? "user" : "assistant";
            currentChatHistory.push({ role: roleForHistory, content: msg.content });
        });

        if (currentChatHistory.length > 10) {
            currentChatHistory = currentChatHistory.slice(currentChatHistory.length - 10);
        }

        currentSessionId = sessionId; 
        loadSessions(); // Pentru a actualiza clasa "active"

    } catch (error) {
        console.error("Eroare la încărcarea istoricului:", error);
    }
}

// --- TRIMITEREA MESAJELOR ---

async function sendMessage() {
    const input = document.getElementById("message-input");
    const message = input.value.trim();
    if (!message) return;

    appendMessage(message, "user");
    input.value = "";

    currentChatHistory.push({ role: "user", content: message });

    if (currentChatHistory.length > 10) {
        currentChatHistory = currentChatHistory.slice(currentChatHistory.length - 10);
    }

    const token = localStorage.getItem("access_token");
    const selectedModel = document.getElementById("model-selector").value;
    const isQuickChat = document.getElementById("quick-chat-toggle").checked;

    try {
        const response = await fetch(`${API_URL}/api/chat/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({
                message: message,
                model: selectedModel,
                session_id: currentSessionId,
                is_quick_chat: isQuickChat,
                history: currentChatHistory 
            })
        });

        if (response.status === 401) return logout();
        const data = await response.json();

        if (!response.ok) {
            appendMessage(`⚠️ Eroare: ${data.detail}`, "ai");
            currentChatHistory.pop();
            return;
        }

        // SALVĂM ID-UL SESIUNII DUPĂ PRIMUL MESAJ (aici era marele bug!)
        if (data.session_id) {
            currentSessionId = data.session_id;
        }

        appendMessage(data.response, "ai");
        currentChatHistory.push({ role: "assistant", content: data.response });

        document.getElementById("credit-count").innerText = data.remaining_credits;

        if (!isQuickChat) {
            loadSessions();
        }

    } catch (error) {
        appendMessage("⚠️ Eroare de conectare.", "ai");
        currentChatHistory.pop(); 
    }
}

function appendMessage(text, sender) {
    const chatBox = document.getElementById("chat-box");
    const div = document.createElement("div");
    div.classList.add("message", `${sender}-message`);
    
    const textDiv = document.createElement("div");
    textDiv.classList.add("text");

    if (sender === "ai") {
        textDiv.innerHTML = marked.parse(text);
    } else {
        textDiv.textContent = text;
    }

    div.appendChild(textDiv);
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight; 
}

// --- PLĂȚI ȘI CREDITE ---

async function buyCredits() {
    const token = localStorage.getItem("access_token");
    try {
        const response = await fetch(`${API_URL}/api/payments/create-checkout-session`, {
            method: "POST",
            headers: { "Authorization": `Bearer ${token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            window.location.href = data.checkout_url; 
        } else {
            alert("Eroare la generarea plății.");
        }
    } catch (error) {
        console.error(error);
    }
}

async function checkPaymentStatus() {
    const urlParams = new URLSearchParams(window.location.search);
    const paymentStatus = urlParams.get('payment');
    const sessionId = urlParams.get('session_id');
    const token = localStorage.getItem("access_token");

    if (paymentStatus === 'success' && sessionId && token) {
        try {
            const response = await fetch(`${API_URL}/api/payments/verify`, {
                method: "POST",
                headers: { 
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ session_id: sessionId })
            });

            if (response.ok) {
                alert("🎉 Plata a fost confirmată! Ți-au fost adăugate 100 de credite.");
                window.history.replaceState({}, document.title, window.location.pathname);
                getCredits();
            }
        } catch (error) {
            console.error("Eroare la verificarea plății:", error);
        }
    } else if (paymentStatus === 'canceled') {
        alert("Plata a fost anulată. Nu ți-a fost extras niciun ban din cont.");
        window.history.replaceState({}, document.title, window.location.pathname);
    }
}

async function getCredits() {
    const token = localStorage.getItem("access_token");
    if (!token) return; 

    try {
        const response = await fetch(`${API_URL}/api/chat/credits`, { 
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            document.getElementById("credit-count").innerText = data.balance;
        } else {
            console.error("Nu am putut prelua creditele.");
        }
    } catch (error) {
        console.error("Eroare la preluarea creditelor:", error);
    }
}

// --- EDITARE ȘI ȘTERGERE SESIUNI ---

async function renameChat(sessionId, currentTitle) {
    const newTitle = prompt("Introdu noul nume pentru conversație:", currentTitle);
    if (!newTitle || newTitle === currentTitle) return;

    const token = localStorage.getItem("access_token");
    try {
        const response = await fetch(`${API_URL}/api/chat/sessions/${sessionId}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({ title: newTitle })
        });

        if (response.ok) {
            loadSessions(); 
        }
    } catch (error) {
        console.error("Eroare la redenumire:", error);
    }
}

async function deleteChat(sessionId) {
    if (!confirm("Sigur vrei să ștergi definitiv această conversație?")) return;

    const token = localStorage.getItem("access_token");
    try {
        const response = await fetch(`${API_URL}/api/chat/sessions/${sessionId}`, {
            method: "DELETE",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (response.ok) {
            loadSessions(); 
            if (sessionId === currentSessionId) {
                document.getElementById("chat-box").innerHTML = ""; 
                currentSessionId = null;
                currentChatHistory = [];
            }
        }
    } catch (error) {
        console.error("Eroare la ștergere:", error);
    }
}