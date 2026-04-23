let challenges = [];
let currentSessionId = null;

document.addEventListener('DOMContentLoaded', async () => {
    // Check auth
    const token = localStorage.getItem('ai_token');
    const name = localStorage.getItem('ai_candidate_name');
    const role = localStorage.getItem('ai_role');
    
    if (!token) {
        window.location.href = '/';
        return;
    }
    document.getElementById('nav-user').innerText = name || "Candidate";
    
    // Hide Admin link if not admin
    if (role !== 'admin') {
        const adminLink = document.querySelector('a[href="/admin"]');
        if (adminLink) adminLink.style.display = 'none';
    }

    // Fetch challenges dynamically
    try {
        const res = await fetch('/api/challenges', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.status === 401) return logout();
        
        const data = await res.json();
        challenges = data.challenges;
    } catch (e) {
        console.error("Failed to load challenges", e);
    }
    const grid = document.getElementById('challenge-grid');
    
    // Render Challenges
    challenges.forEach(c => {
        const card = document.createElement('div');
        card.className = 'glass-card';
        card.innerHTML = `
            <span class="domain-tag">${c.domain}</span>
            <h3 class="card-title">${c.title}</h3>
            <p class="card-desc">${c.desc}</p>
            <div class="tech-stack">
                ${c.stack.map(tech => `<span class="tech-badge">${tech}</span>`).join('')}
            </div>
        `;
        
        card.addEventListener('click', () => launchSandbox(c));
        grid.appendChild(card);
    });
});

let currentChallenge = null;
let timerInterval = null;
let ideStartTime = null;

async function launchSandbox(challenge) {
    currentChallenge = challenge;
    const modal = document.getElementById('briefing-modal');
    document.getElementById('briefing-title').innerText = `Mission Briefing: ${challenge.title}`;
    document.getElementById('briefing-desc').innerText = challenge.desc;
    modal.classList.add('active');
}

function closeBriefing() {
    document.getElementById('briefing-modal').classList.remove('active');
    currentChallenge = null;
}

async function deployChallenge() {
    if (!currentChallenge) return;
    
    const challenge = currentChallenge;
    closeBriefing();
    
    const modal = document.getElementById('launch-modal');
    const title = document.getElementById('modal-title');
    const terminal = document.getElementById('terminal-output');
    
    modal.classList.add('active');
    title.innerText = `Initializing Sandbox: ${challenge.title}`;
    terminal.innerHTML = '';
    
    const logs = [
        `> Requesting ephemeral sandbox for challenge [${challenge.id}]...`,
        `> Authenticating Candidate session... OK`,
    ];
    
    // Simulate terminal typing
    for (let msg of logs) {
        addTerminalLine(terminal, msg);
        await new Promise(r => setTimeout(r, 800));
    }
    
    try {
        const token = localStorage.getItem('ai_token');
        // Call the FastAPI Orchestrator
        const res = await fetch('/session/start', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                candidate_id: "cand_" + Math.random().toString(36).substr(2, 9),
                challenge_id: challenge.id
            })
        });
        
        const data = await res.json();
        
        if (res.ok) {
            addTerminalLine(terminal, `> Orchestrator response: ${data.status.toUpperCase()}`);
            addTerminalLine(terminal, `> Provisioning AWS ECS Task...`);
            await new Promise(r => setTimeout(r, 1500));
            addTerminalLine(terminal, `> Injecting Adversary Proxy middleware... OK`);
            addTerminalLine(terminal, `> Sandbox Ready. Launching embedded IDE...`);
            
            const countdownLine = document.createElement('p');
            countdownLine.style.color = 'var(--accent-pink)';
            countdownLine.style.fontWeight = 'bold';
            countdownLine.innerText = `\n> STARTING WORKSPACE IN 3...`;
            terminal.appendChild(countdownLine);
            terminal.scrollTop = terminal.scrollHeight;
            
            let seconds = 3;
            const timer = setInterval(() => {
                seconds--;
                if (seconds > 0) {
                    countdownLine.innerText = `\n> STARTING WORKSPACE IN ${seconds}...`;
                }
            }, 1000);
            
            setTimeout(() => {
                clearInterval(timer);
                modal.classList.remove('active');
                
                // Embed the IDE in the page via iframe
                const ideContainer = document.getElementById('ide-container');
                const ideFrame = document.getElementById('ide-frame');
                const titleText = document.querySelector('.premium-text');
                
                // Update title to show which challenge is active
                titleText.innerText = `Active Session: ${challenge.title}`;
                
                // Minimize UI and show IDE
                document.body.classList.add('ide-active');
                
                // Save session ID
                currentSessionId = data.session_id;
                document.getElementById('submit-btn').innerText = "Final Submit";
                
                ideFrame.src = `http://localhost:8443/?folder=/config/workspace/${challenge.id}/candidate_workspace`;
                ideContainer.style.display = 'block';
                startTimer();
            }, 3000);
        } else {
            addTerminalLine(terminal, `> ERROR: ${data.detail}`, "red");
            setTimeout(() => modal.classList.remove('active'), 3000);
        }
    } catch (err) {
        addTerminalLine(terminal, `> NETWORK ERROR: Could not connect to API.`, "red");
        setTimeout(() => modal.classList.remove('active'), 3000);
    }
}

function startTimer() {
    ideStartTime = Date.now();
    const timerDisplay = document.getElementById('ide-timer');
    timerInterval = setInterval(() => {
        const diff = Math.floor((Date.now() - ideStartTime) / 1000);
        const mins = String(Math.floor(diff / 60)).padStart(2, '0');
        const secs = String(diff % 60).padStart(2, '0');
        timerDisplay.innerText = `${mins}:${secs}`;
    }, 1000);
}

function stopTimer() {
    if (timerInterval) clearInterval(timerInterval);
    document.getElementById('ide-timer').innerText = "00:00";
}

function closeIDE() {
    const ideContainer = document.getElementById('ide-container');
    const ideFrame = document.getElementById('ide-frame');
    const titleText = document.querySelector('.premium-text');
    
    // Restore UI
    document.body.classList.remove('ide-active');
    titleText.innerText = "Select Simulation";
    
    ideContainer.style.display = 'none';
    ideFrame.src = ''; // Clear the iframe to free memory
    currentSessionId = null;
    currentChallenge = null;
    stopTimer();
}

async function testSolution() {
    if (!currentSessionId) return;
    
    const btn = document.getElementById('test-btn');
    const originalText = btn.innerText;
    btn.innerText = "Testing...";
    btn.disabled = true;
    
    try {
        const token = localStorage.getItem('ai_token');
        const res = await fetch('/api/evaluate/test', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ session_id: currentSessionId, challenge_id: currentChallenge.id })
        });
        
        if (res.status === 401) return logout();
        const data = await res.json();
        
        if (res.ok) {
            alert(`Test Results:\n\nVerdict: ${data.verdict}\nFeedback: ${data.feedback}\n\nYou can keep coding or Final Submit.`);
        } else {
            alert("Failed to run tests.");
        }
    } catch (err) {
        console.error(err);
        alert("Error testing solution.");
    }
    
    btn.innerText = originalText;
    btn.disabled = false;
}

async function submitSolution() {
    if (!currentSessionId) return;
    
    const btn = document.getElementById('submit-btn');
    btn.innerText = "Evaluating...";
    btn.disabled = true;
    
    try {
        const token = localStorage.getItem('ai_token');
        const res = await fetch('/api/evaluate/submit', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ session_id: currentSessionId, challenge_id: currentChallenge.id })
        });
        
        if (res.status === 401) return logout();
        const data = await res.json();
        
        if (res.ok) {
            btn.innerText = `Verdict: ${data.verdict}`;
            alert(`Final Evaluation Complete!\nVerdict: ${data.verdict}\n\nFeedback: ${data.feedback}`);
            closeIDE();
        } else {
            btn.innerText = "Error";
            alert("Failed to evaluate solution.");
        }
    } catch (err) {
        btn.innerText = "Error";
        console.error(err);
    }
    
    btn.disabled = false;
}

function logout() {
    document.querySelector('main').classList.remove('page-fade-in');
    document.querySelector('main').classList.add('page-fade-out');
    setTimeout(() => {
        localStorage.removeItem('ai_token');
        localStorage.removeItem('ai_role');
        localStorage.removeItem('ai_candidate_name');
        window.location.href = '/';
    }, 400);
}

function addTerminalLine(container, text, color = null) {
    const p = document.createElement('p');
    p.innerText = text;
    if (color) p.style.color = color;
    container.appendChild(p);
    container.scrollTop = container.scrollHeight;
}
