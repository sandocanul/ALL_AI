const API_URL = "https://all-ai-1-ndsb.onrender.com";
let currentChatHistory = []; // Aici ținem minte mesajele din conversația curentă
// Verificăm dacă suntem deja logați
window.onload = () => {
    if (localStorage.getItem("access_token")) {
        showChat();
    }
};

// Funcția pentru LOGARE (Intră în contul existent)
async function login() {
    const user = document.getElementById("username").value;
    const pass = document.getElementById("password").value;

    if (!user || !pass) {
        alert("Introdu username și parola!");
        return;
    }

    try {
        // FastAPI OAuth2 cere ca datele să fie trimise ca x-www-form-urlencoded
        const formData = new URLSearchParams();
        // AICI E SECRETUL: îi dăm email-ul fals în loc de simplul username!
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
            // 1. Salvăm token-ul în memoria browserului (ca să-l folosească loadChatHistory)
            localStorage.setItem("access_token", data.access_token);
            
            // 2. Ascundem logarea și arătăm chat-ul (aici folosești ID-urile tale corecte)
            // Adăugăm clasa ascunsă pe cutia de logare
            loadSessions();
document.getElementById("auth-container").classList.add("hidden");

// Scoatem clasa ascunsă de pe cutia de chat ca să se vadă
document.getElementById("chat-container").classList.remove("hidden");
            
            // 3. Pornim aplicația! (Aducem sesiunile vechi)
            // Dacă ai o funcție care face asta, de obicei e loadSessions() sau showChat()
            if (typeof loadSessions === "function") {
                loadSessions(); 
                console.log("Logare terminată complet! Chat-ul ar trebui să fie vizibil.");
            } else if (typeof showChat === "function") {
                showChat();
            }
        } else {
            const errorData = await response.json();
            alert("Eroare la login: " + JSON.stringify(errorData));
        }
    } catch (error) {
        console.error("Eroare la login:", error);
    }
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
            // AICI ESTE MODIFICAREA MAGICA: Am adăugat un email generat automat
            body: JSON.stringify({ username: user, email: user + "@test.com", password: pass })
        });

        if (response.ok) {
            msg.innerText = "Cont creat cu succes! Acum te poți loga.";
            msg.style.color = "#10b981"; // Verde
            // Opțional: îi completăm noi parola ca să dea doar click pe Logare
        } else {
            const data = await response.json();
            msg.innerText = data.detail || "Acest nume de utilizator există deja.";
            msg.style.color = "#ef4444"; // Roșu
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

// Funcția care schimbă ecranele (ascunde Login, arată Chat)
function showChat() {
    document.getElementById("auth-container").classList.add("hidden");
    document.getElementById("chat-container").classList.remove("hidden");
    
    // Apelăm funcția nouă pentru Sidebar!
    loadSessions(); 
    checkPaymentStatus();
    getCredits();
}


function handleEnter(event) {
    if (event.key === "Enter") sendMessage();
}
let currentSessionId = null;

// 1. Încarcă sesiunile în Sidebar
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

        if (sessions.length === 0) {
            createNewSession();
            return;
        }

        // Trecem prin fiecare sesiune primită de la server
        sessions.forEach(session => {
            // 1. Creăm elementul principal de listă
            const li = document.createElement("li");
            li.className = "session-item";
            if (session.id === currentSessionId) {
                li.classList.add("active");
            }

            // 2. Creăm titlul care poate fi apăsat pentru a încărca chat-ul
            const titleSpan = document.createElement("span");
            titleSpan.className = "session-title";
            titleSpan.innerText = session.title;
            titleSpan.onclick = () => loadChatHistory(session.id); // Aici încarcă chat-ul

            // 3. Creăm containerul pentru butoane
            const actionsDiv = document.createElement("div");
            actionsDiv.className = "session-actions";

            // 4. Creăm butonul de Edit
            const editBtn = document.createElement("button");
            editBtn.title = "Redenumește";
            editBtn.innerText = "✏️";
            editBtn.onclick = (e) => {
                e.stopPropagation(); // OPREȘTE click-ul să se ducă la 'li'
                renameChat(session.id, session.title);
            };

            // 5. Creăm butonul de Ștergere
            const deleteBtn = document.createElement("button");
            deleteBtn.title = "Șterge";
            deleteBtn.innerText = "🗑️";
            deleteBtn.onclick = (e) => {
                e.stopPropagation(); // OPREȘTE click-ul să se ducă la 'li'
                deleteChat(session.id);
            };

            // Adăugăm butoanele în div-ul de acțiuni
            actionsDiv.appendChild(editBtn);
            actionsDiv.appendChild(deleteBtn);

            // Asamblăm totul în `li`
            li.appendChild(titleSpan);
            li.appendChild(actionsDiv);

            // Adăugăm `li`-ul în lista principală din stânga
            sessionsList.appendChild(li);
        });

    // AICI ERA PROBLEMA: lipsea închiderea blocului "try" și "catch-ul" pentru erori!
    } catch (error) {
        console.error("Eroare la încărcarea sesiunilor:", error);
    }
}

// 2. Creează o conversație nouă
async function createNewSession() {
    currentChatHistory = [];
    const token = localStorage.getItem("access_token");
    const response = await fetch(`${API_URL}/api/chat/sessions`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
    });
    const newSession = await response.json();
    currentSessionId = newSession.id;
    
    document.getElementById("chat-box").innerHTML = "";
    appendMessage("Am creat o conversație nouă! Cu ce te pot ajuta?", "ai");
    loadSessions(); // Reîmprospătează lista
}

// 3. Încarcă istoricul pentru o sesiune specifică
async function loadChatHistory(sessionId) {
    currentSessionId = sessionId;
    loadSessions(); // Pentru a actualiza clasa "active" pe butonul apăsat

    const token = localStorage.getItem("access_token");
    const response = await fetch(`${API_URL}/api/chat/history/${sessionId}`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    
    const messages = await response.json();
    const chatBox = document.getElementById("chat-box");
    chatBox.innerHTML = ""; 

    messages.forEach(msg => appendMessage(msg.content, msg.sender));
    
    if (messages.length === 0) {
         appendMessage("Salut! Aceasta este o conversație nouă.", "ai");
    }
}

async function sendMessage() {
    const input = document.getElementById("message-input");
    const message = input.value.trim();
    if (!message) return;

    appendMessage(message, "user");
    input.value = "";

    // 1. Adăugăm mesajul tău în istoricul conversației
    currentChatHistory.push({ role: "user", content: message });

    // 2. Tăiem istoricul dacă e prea lung (păstrăm ultimele 10 mesaje = 5 întrebări și 5 răspunsuri)
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
                history: currentChatHistory // <--- AICI ESTE SECRETUL: trimitem toată lista!
            })
        });

        if (response.status === 401) return logout();
        const data = await response.json();

        if (!response.ok) {
            appendMessage(`⚠️ Eroare: ${data.detail}`, "ai");
            // Dacă dă eroare, scoatem ultimul tău mesaj din istoric ca să nu încurcăm AI-ul
            currentChatHistory.pop();
            return;
        }

        appendMessage(data.response, "ai");
        
        // 3. Adăugăm și răspunsul AI-ului în istoric ca să știe ce ți-a răspuns
        currentChatHistory.push({ role: "assistant", content: data.response });

        document.getElementById("credit-count").innerText = data.remaining_credits;

        if (!isQuickChat) {
            loadSessions();
        }

    } catch (error) {
        appendMessage("⚠️ Eroare de conectare.", "ai");
        currentChatHistory.pop(); // Scoatem mesajul pe care am încercat să-l trimitem, dar a picat
    }
}

// CA SĂ FIE TOTUL BINE: La funcția ta "createNewSession()" (dacă ai),
// adaugă linia: currentChatHistory = []; ca să se șteargă memoria când începi un chat nou.

function appendMessage(text, sender) {
    const chatBox = document.getElementById("chat-box");
    
    // Cream bula principală a mesajului
    const div = document.createElement("div");
    div.classList.add("message", `${sender}-message`);
    
    // Cream zona efectivă de text din interiorul bulei
    const textDiv = document.createElement("div");
    textDiv.classList.add("text");

    // Aici aplicăm regula pentru formatare
    if (sender === "ai") {
        // AI-ul primește formatare Markdown (titluri, bold, liste, cod)
        textDiv.innerHTML = marked.parse(text);
    } else {
        // Mesajul utilizatorului rămâne text simplu (pentru securitate și simplitate)
        textDiv.textContent = text;
    }

    // Punem textul în bulă, și bula pe ecran
    div.appendChild(textDiv);
    chatBox.appendChild(div);
    
    // Autoscroll în jos
    chatBox.scrollTop = chatBox.scrollHeight; 
}
// 1. Funcția care cere link-ul de la Stripe și te trimite acolo
async function buyCredits() {
    const token = localStorage.getItem("access_token");
    try {
        const response = await fetch(`${API_URL}/api/payments/create-checkout-session`, {
            method: "POST",
            headers: { "Authorization": `Bearer ${token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            // Redirecționăm utilizatorul către pagina securizată de plată Stripe
            window.location.href = data.checkout_url; 
        } else {
            alert("Eroare la generarea plății.");
        }
    } catch (error) {
        console.error(error);
    }
}

// 2. Funcția care verifică dacă te-ai întors victorios de la plata Stripe
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
                // Curățăm URL-ul ca să nu facă refresh de 100 de ori cu același mesaj
                window.history.replaceState({}, document.title, window.location.pathname);
                // (Opțional: aici ai putea apela o funcție getCredits() ca să actualizezi numărul pe ecran instant)
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
// Funcție care preia numărul actual de credite de la server și îl afișează
async function getCredits() {
    const token = localStorage.getItem("access_token");
    if (!token) return; // Dacă nu suntem logați, nu facem nimic

    try {
        const response = await fetch(`${API_URL}/api/chat/credits`, { // presupun că asta e ruta din backend
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            // Actualizăm numărul de pe ecran
            document.getElementById("credit-count").innerText = data.balance;
        } else {
            console.error("Nu am putut prelua creditele.");
        }
    } catch (error) {
        console.error("Eroare la preluarea creditelor:", error);
    }
}
// Funcția de Redenumire
async function renameChat(sessionId, currentTitle) {
    // Cerem un nume nou de la utilizator (folosim un prompt simplu de browser)
    const newTitle = prompt("Introdu noul nume pentru conversație:", currentTitle);
    
    // Dacă dă cancel sau lasă gol, oprim funcția
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
            loadSessions(); // Reîncărcăm meniul din stânga să arate noul nume
        }
    } catch (error) {
        console.error("Eroare la redenumire:", error);
    }
}

// Funcția de Ștergere
async function deleteChat(sessionId) {
    // Cerem confirmare, să nu șteargă din greșeală!
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
            loadSessions(); // Actualizăm meniul
            
            // Opțional: Dacă ștergem conversația pe care o citim acum, golim ecranul principal
            // Dacă ai o variabilă globală care ține ID-ul chat-ului curent (ex: currentSessionId), folosește-o aici.
            document.getElementById("chat-box").innerHTML = ""; 
        }
    } catch (error) {
        console.error("Eroare la ștergere:", error);
    }
}
// --- FUNCȚII PENTRU SESIUNILE DE CHAT ---

// 1. Încarcă lista de sesiuni în bara din stânga
async function loadSessions() {
    const token = localStorage.getItem("access_token");
    if (!token) return;

    try {
        const response = await fetch(`${API_URL}/api/chat/sessions`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        
        if (!response.ok) return;
        
        const sessions = await response.json();
        const sessionsList = document.getElementById("sessions-list");
        sessionsList.innerHTML = ""; // Curățăm lista existentă

        // Creăm un buton pentru fiecare sesiune găsită în baza de date
        sessions.forEach(session => {
            const btn = document.createElement("button");
            btn.classList.add("session-btn");
            // Afișăm un titlu scurt
            btn.innerText = `💬 ${session.title}`;
            
            // Când apeși pe el, încarcă mesajele din sesiunea respectivă
            btn.onclick = () => loadSessionHistory(session.id);
            
            sessionsList.appendChild(btn);
        });
    } catch (error) {
        console.error("Eroare la încărcarea sesiunilor:", error);
    }
}

// 2. Încarcă mesajele unei sesiuni vechi pe ecran
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
        chatBox.innerHTML = ""; // Curățăm ecranul actual
        currentChatHistory = []; // Golește și memoria curentă

        // Pentru fiecare mesaj din baza de date, îl punem pe ecran și în memoria curentă
        messages.forEach(msg => {
            // "msg.sender" vine din baza de date ("user" sau "ai")
            appendMessage(msg.content, msg.sender);
            
            // Reconstruim memoria (Sliding Window) ca AI-ul să poată continua de unde a rămas
            const roleForHistory = msg.sender === "user" ? "user" : "assistant";
            currentChatHistory.push({ role: roleForHistory, content: msg.content });
        });

        // Tăiem memoria la ultimele 10 dacă cumva sesiunea era foarte lungă
        if (currentChatHistory.length > 10) {
            currentChatHistory = currentChatHistory.slice(currentChatHistory.length - 10);
        }

        // Setăm sesiunea curentă ca să știe backend-ul unde să salveze noile mesaje
        currentSessionId = sessionId; 

    } catch (error) {
        console.error("Eroare la încărcarea istoricului:", error);
    }
}

// 3. Butonul "Chat Nou" din stânga sus
function createNewSession() {
    currentSessionId = null; // Backend-ul va crea un ID nou când trimiți primul mesaj
    currentChatHistory = []; // AI-ul capătă "amnezie"
    document.getElementById("chat-box").innerHTML = ""; // Curățăm ecranul
}

// Apelăm loadSessions() de fiecare dată când utilizatorul se loghează sau când se încarcă pagina
// (Adaugă `loadSessions()` în funcția ta de login, după ce salvezi token-ul!)
// Când se încarcă pagina, dacă avem token de logare, încărcăm direct sesiunile
document.addEventListener("DOMContentLoaded", () => {
    const token = localStorage.getItem("access_token");
    if (token) {
        loadSessions();
    }
});
// --- FUNCȚII PENTRU SESIUNILE DE CHAT ---

// 1. Încarcă lista de sesiuni în bara din stânga
async function loadSessions() {
    const token = localStorage.getItem("access_token");
    if (!token) return;

    try {
        const response = await fetch(`${API_URL}/api/chat/sessions`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        
        if (!response.ok) return;
        
        const sessions = await response.json();
        const sessionsList = document.getElementById("sessions-list");
        sessionsList.innerHTML = ""; // Curățăm lista existentă

        // Creăm un buton pentru fiecare sesiune găsită în baza de date
        sessions.forEach(session => {
            const btn = document.createElement("button");
            btn.classList.add("session-btn");
            // Afișăm un titlu scurt
            btn.innerText = `💬 ${session.title}`;
            
            // Când apeși pe el, încarcă mesajele din sesiunea respectivă
            btn.onclick = () => loadSessionHistory(session.id);
            
            sessionsList.appendChild(btn);
        });
    } catch (error) {
        console.error("Eroare la încărcarea sesiunilor:", error);
    }
}

// 2. Încarcă mesajele unei sesiuni vechi pe ecran
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
        chatBox.innerHTML = ""; // Curățăm ecranul actual
        currentChatHistory = []; // Golește și memoria curentă

        // Pentru fiecare mesaj din baza de date, îl punem pe ecran și în memoria curentă
        messages.forEach(msg => {
            // "msg.sender" vine din baza de date ("user" sau "ai")
            appendMessage(msg.content, msg.sender);
            
            // Reconstruim memoria (Sliding Window) ca AI-ul să poată continua de unde a rămas
            const roleForHistory = msg.sender === "user" ? "user" : "assistant";
            currentChatHistory.push({ role: roleForHistory, content: msg.content });
        });

        // Tăiem memoria la ultimele 10 dacă cumva sesiunea era foarte lungă
        if (currentChatHistory.length > 10) {
            currentChatHistory = currentChatHistory.slice(currentChatHistory.length - 10);
        }

        // Setăm sesiunea curentă ca să știe backend-ul unde să salveze noile mesaje
        currentSessionId = sessionId; 

    } catch (error) {
        console.error("Eroare la încărcarea istoricului:", error);
    }
}

// 3. Butonul "Chat Nou" din stânga sus
function createNewSession() {
    currentSessionId = null; // Backend-ul va crea un ID nou când trimiți primul mesaj
    currentChatHistory = []; // AI-ul capătă "amnezie"
    document.getElementById("chat-box").innerHTML = ""; // Curățăm ecranul
}

// Apelăm loadSessions() de fiecare dată când utilizatorul se loghează sau când se încarcă pagina
// (Adaugă `loadSessions()` în funcția ta de login, după ce salvezi token-ul!)