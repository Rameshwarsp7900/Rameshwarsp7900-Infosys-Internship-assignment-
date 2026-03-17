document.addEventListener('DOMContentLoaded', () => {
    // State
    let currentData = null;
    let radarChart = null;
    let sentimentChart = null;

    // Dynamic API discovery: use absolute URL if local, relative if deployed
    const API_BASE = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || window.location.protocol === 'file:')
        ? 'http://localhost:5000/api'
        : '/api';

    // UI Elements
    const tabs = document.querySelectorAll('nav li');
    const tabContents = document.querySelectorAll('.tab-content');
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const analyzeBtn = document.getElementById('analyze-btn');
    const agentNameInput = document.getElementById('agent-name');
    const progressContainer = document.getElementById('upload-progress');
    const progressBar = document.querySelector('.progress-bar');

    // Tab Switching
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const target = tab.getAttribute('data-tab');
            switchTab(target);
        });
    });

    function switchTab(target) {
        tabs.forEach(t => t.classList.remove('active'));
        document.querySelector(`nav li[data-tab="${target}"]`).classList.add('active');

        tabContents.forEach(content => {
            content.classList.remove('active');
            if (content.id === `tab-${target}`) {
                content.classList.add('active');
            }
        });

        if (target === 'batch') loadBatchResults();
        if (target === 'leaderboard') loadLeaderboard();
        if (target === 'scorecard' && !currentData) switchTab('upload');
    }

    // File Upload Handlers
    dropZone.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            analyzeBtn.disabled = false;
            dropZone.querySelector('p').textContent = e.target.files[0].name;
        }
    });

    analyzeBtn.addEventListener('click', async () => {
        const file = fileInput.files[0];
        const agentName = agentNameInput.value || 'Unknown Agent';

        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);
        formData.append('agent_name', agentName);

        // Show progress
        progressContainer.classList.remove('hidden');
        progressBar.style.width = '30%';
        analyzeBtn.disabled = true;

        try {
            const response = await fetch(`${API_BASE}/upload`, {
                method: 'POST',
                body: formData
            });

            progressBar.style.width = '100%';
            const result = await response.json();

            if (result.error) throw new Error(result.error);

            currentData = result;
            displayScorecard(result);
            switchTab('scorecard');
            loadAlerts();

        } catch (error) {
            alert(`Analysis failed: ${error.message}`);
        } finally {
            progressContainer.classList.add('hidden');
            analyzeBtn.disabled = false;
        }
    });

    function displayScorecard(data) {
        document.getElementById('sc-agent-name').textContent = data.agent_name;
        document.getElementById('sc-date').textContent = `${data.date} | ID: ${data.id}`;
        document.getElementById('sc-overall-score').textContent = data.overall_score;

        renderRadarChart(data.categories);
        renderSentimentTimeline(data.sentiment_timeline);
        renderParameters(data.parameters, data.reasoning);
        renderCoaching(data.coaching);
        renderViolations(data.violations);
        renderTranscript(data.transcript);
    }

    function renderRadarChart(categories) {
        const ctx = document.getElementById('radarChart').getContext('2d');
        if (radarChart) radarChart.destroy();

        radarChart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Communication', 'Problem Solving', 'Efficiency', 'Compliance'],
                datasets: [{
                    label: 'Score',
                    data: [
                        categories.communication,
                        categories.problem_solving,
                        categories.efficiency,
                        categories.compliance
                    ],
                    backgroundColor: 'rgba(99, 102, 241, 0.2)',
                    borderColor: 'rgb(99, 102, 241)',
                    pointBackgroundColor: 'rgb(99, 102, 241)',
                }]
            },
            options: {
                scales: {
                    r: { beginAtZero: true, max: 5 }
                }
            }
        });
    }

    function renderSentimentTimeline(timeline) {
        const ctx = document.getElementById('sentimentChart').getContext('2d');
        if (sentimentChart) sentimentChart.destroy();

        const agentData = timeline.filter(t => t.role === 'agent');
        const customerData = timeline.filter(t => t.role === 'customer');

        sentimentChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: timeline.map(t => Math.round(t.time) + 's'),
                datasets: [
                    {
                        label: 'Agent Sentiment',
                        data: timeline.map(t => t.role === 'agent' ? t.score : null),
                        borderColor: '#6366f1',
                        tension: 0.3,
                        spanGaps: true
                    },
                    {
                        label: 'Customer Sentiment',
                        data: timeline.map(t => t.role === 'customer' ? t.score : null),
                        borderColor: '#a855f7',
                        tension: 0.3,
                        spanGaps: true
                    }
                ]
            },
            options: {
                scales: {
                    y: { min: -1, max: 1 }
                }
            }
        });
    }

    function renderParameters(params, reasoning) {
        const container = document.getElementById('parameters-list');
        container.innerHTML = '';

        Object.entries(params).forEach(([key, val]) => {
            const item = document.createElement('div');
            item.className = 'param-item';
            item.innerHTML = `
                <div class="param-info">
                    <strong>${key.replace(/_/g, ' ').toUpperCase()}</strong>
                    <span>${val}/5</span>
                </div>
                <div class="progress-bg"><div class="progress-fill" style="width: ${val*20}%"></div></div>
                <p class="reasoning">${reasoning[key] || ''}</p>
            `;
            container.appendChild(item);
        });
    }

    function renderCoaching(coaching) {
        const container = document.getElementById('coaching-list');
        container.innerHTML = coaching.map(c => `
            <div class="coaching-item">
                <span class="badge ${c.priority.toLowerCase()}">${c.priority} Priority</span>
                <h4>${c.area}</h4>
                <p><strong>Issue:</strong> ${c.issue}</p>
                <p class="moment"><em>"${c.transcript_moment}"</em></p>
                <p><strong>Action:</strong> ${c.action}</p>
            </div>
        `).join('');
    }

    function renderViolations(violations) {
        const container = document.getElementById('violations-list');
        if (violations.length === 0) {
            container.innerHTML = '<p class="success-text">No compliance violations detected.</p>';
            return;
        }
        container.innerHTML = violations.map(v => `
            <div class="violation-item">
                <strong>Banned Phrase:</strong> "${v.phrase}"
                <p>Location: ${v.timestamp}s</p>
                <p>Snippet: ...${v.text_snippet}...</p>
            </div>
        `).join('');
    }

    function renderTranscript(transcript) {
        const container = document.getElementById('transcript-container');
        container.innerHTML = transcript.map(t => `
            <div class="utterance ${t.role}">
                <div class="meta">${t.role.toUpperCase()} | ${Math.round(t.start_time || 0)}s</div>
                <div class="text">${t.text}</div>
            </div>
        `).join('');
    }

    async function loadBatchResults() {
        const response = await fetch(`${API_BASE}/results`);
        const results = await response.json();
        const body = document.getElementById('batch-results-body');
        body.innerHTML = results.map(r => `
            <tr>
                <td>${r.agent_name}</td>
                <td>${r.date}</td>
                <td><strong>${r.overall_score}</strong></td>
                <td>${r.categories.communication}</td>
                <td>${r.categories.problem_solving}</td>
                <td>${r.categories.efficiency}</td>
                <td>${r.categories.compliance}</td>
                <td><button onclick="viewResult('${r.id}')" class="btn-sm">View</button></td>
            </tr>
        `).join('');
    }

    async function loadLeaderboard() {
        const response = await fetch(`${API_BASE}/leaderboard`);
        const leaderboard = await response.json();
        const container = document.getElementById('leaderboard-container');
        container.innerHTML = leaderboard.map((a, i) => `
            <div class="card leaderboard-card">
                <div class="rank">#${i+1}</div>
                <div class="agent-name">${a.name}</div>
                <div class="stats">
                    <span>Score: ${a.overall_score}</span>
                    <span>Calls: ${a.calls_processed}</span>
                </div>
                <div class="trend ${a.trend}">${a.trend === 'improving' ? '↑' : a.trend === 'declining' ? '↓' : '→'}</div>
            </div>
        `).join('');
    }

    async function loadAlerts() {
        const response = await fetch(`${API_BASE}/alerts`);
        const alerts = await response.json();
        document.getElementById('alert-count').textContent = alerts.length;
        const list = document.getElementById('alerts-list');
        list.innerHTML = alerts.map(a => `
            <div class="alert-item mini">
                <strong>${a.type}</strong>
                <span>${a.agent_name} - Score: ${a.score}</span>
            </div>
        `).join('');
    }

    // Initialize
    loadAlerts();
});

// Global function for view button
window.viewResult = async (id) => {
    // This would typically fetch from state or API
    // For this simple SPA we'll just re-display from state
    alert("Viewing " + id);
};
